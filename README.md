# Spyre vLLM Big Picture

Status: Working note

Last updated: 2026-03-16

## Purpose

This note is the broad planning view for Spyre + vLLM work across:

- the current `vllm_spyre` stack
- the emerging `vllm_spyre_next` stack
- KV reuse / KV offload / P-D disaggregation
- multi-Spyre and distributed support
- the transition from the current compiler/runtime contracts to the next ones

This note is intentionally broader than the in-tree research/RFC documents. It is meant to help decide priorities, validation order, and where to watch for external changes.

## Working Links

- [Live tracker](./LIVE_TRACKER.md)
- Working research draft in `toddllm/vllm-spyre`:
  [spyre-kv-offload-research.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-research.md)
- Working RFC draft in `toddllm/vllm-spyre`:
  [spyre-kv-offload-rfc-draft.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-rfc-draft.md)

This repo is intended to be the higher-level tracking/meta layer. Lower-level
RFCs, research notes, PRs, and implementation details should continue to live
in the most relevant source repo and then get linked here.

## Naming

To keep the discussion clear, this note uses the following names consistently.

- `current stack` / `old stack`
  - `vllm_spyre`
  - custom `SpyrePlatform`, scheduler, worker, model runner
  - FMS model code and FMS attention path
  - `torch.compile` through the current Spyre integration path
  - SendNN / DeepTools style execution path

- `current compiler stack`
  - the compiler/runtime path underneath the current stack
  - today this still revolves around the existing DeepTools-oriented contracts
  - on the torch-spyre side this is still represented by `SuperDSC-Bundle` +
    `SpyreCode` / `JobPlan`

- `next stack` / `Spyre-Next`
  - `vllm_spyre_next`
  - intended to consume upstream vLLM modeling code directly
  - intended to rely on `torch-spyre` for the device/runtime/compiler path
  - intended to reuse more upstream vLLM scheduling / compilation behavior

- `future compiler stack`
  - the compiler/runtime path torch-spyre is moving toward after the current
    `SuperDSC-Bundle` / `SpyreCode` interface
  - represented publicly by the `KTIR` direction

The important distinction is:

- `current stack` vs `next stack` is a `vllm-spyre` plugin question
- `current compiler stack` vs `future compiler stack` is a `torch-spyre`
  compiler/runtime question

Those transitions are related, but they are not the same transition.

## Where We Have Been

The original `vllm_spyre` architecture made sense because:

1. vLLM modeling code was not a good fit for `torch.compile`
2. Spyre compiler/runtime constraints forced custom scheduling, batching, and
   model-execution logic
3. using FMS and a smaller custom surface reduced upstream breakage risk

That produced a plugin that worked, but at the cost of:

- custom scheduler logic
- custom worker/model-runner logic
- custom attention / KV management path
- dependence on FMS modeling code instead of upstream vLLM modeling code
- limited reuse of upstream vLLM compiler integrations

The `vllm-spyre-next` direction exists because those assumptions are changing:

- upstream vLLM now leans hard on `torch.compile`
- torch-spyre is trying to make Spyre look more like a first-class PyTorch
  device/backend
- the torch-spyre runtime/compiler surface is being reorganized in ways that
  should make a thinner vLLM plugin more plausible over time

## Architecture Snapshot: Current Stack

```text
                      CURRENT STACK / OLD STACK
                   (vllm_spyre + FMS + SendNN path)

  User / OpenAI API / LLM.generate
                 |
                 v
         upstream vLLM engine core
                 |
                 v
     +----------------------------------+
     | vllm_spyre plugin                |
     |                                  |
     |  - SpyrePlatform                 |
     |  - custom scheduler              |
     |  - custom worker                 |
     |  - custom model runner           |
     +----------------------------------+
                 |
                 v
     +----------------------------------+
     | execution model                  |
     |                                  |
     |  - FMS model code                |
     |  - FMS attention / KV handling   |
     |  - custom warmup / batching      |
     +----------------------------------+
                 |
                 v
          torch.compile (Dynamo level)
                 |
        +--------+---------+
        |                  |
        v                  v
     sendnn             inductor
        |
        v
   DeepTools / current runtime
        |
        v
       AIU
```

Properties of this design point:

- good near-term hardware enablement
- significant custom code
- FMS dependency
- no native reuse of upstream vLLM modeling code
- KV connector integration has to be added around the worker/model-runner seam

## Architecture Snapshot: Next Stack

```text
                        NEXT STACK / SPYRE-NEXT
          (vllm_spyre_next + torch-spyre + upstream vLLM modeling)

  User / OpenAI API / LLM.generate
                 |
                 v
         upstream vLLM engine core
                 |
                 v
     +----------------------------------+
     | thinner Spyre plugin             |
     |                                  |
     |  - Spyre-specific platform       |
     |  - likely Spyre worker           |
     |  - likely Spyre model runner     |
     |  - no FMS dependency             |
     +----------------------------------+
                 |
                 v
     +----------------------------------+
     | upstream vLLM execution model    |
     |                                  |
     |  - upstream model code           |
     |  - Spyre attention backend       |
     |  - upstream scheduler behavior   |
     +----------------------------------+
                 |
                 v
        torch.compile / Inductor path
                 |
                 v
     +----------------------------------+
     | torch-spyre device/runtime       |
     |                                  |
     |  - device model                  |
     |  - allocator / tensor layout     |
     |  - stream support                |
     |  - copy path                     |
     |  - distributed backend           |
     +----------------------------------+
                 |
                 v
      current compiler contract today:
        SuperDSC-Bundle -> SpyreCode / JobPlan
                 |
      future compiler contract later:
                   KTIR
                 |
                 v
                AIU
```

Properties of this design point:

- potentially far less plugin-specific code
- more direct reuse of upstream vLLM behavior
- much more dependent on torch-spyre runtime/compiler maturity
- makes multi-Spyre and distributed support much more central

## KV Reuse / KV Offload / PD Disagg: Current Stack

### 1. Current-stack local KV reuse / offload direction

```text
   current stack request
         |
         v
   current scheduler emits
   kv_connector_metadata
         |
         v
   SpyreKVConnectorBridge
   (worker-side, synchronous)
         |
         v
   staging tensors <-> live FMS KV
         |
         v
   connector medium
     |           |
     |           +--> host-memory reuse store
     |
     +--> future transport / offload target
```

The important point is that the seam is worker-side and staging-based.

That is a workable near-term seam, but it is not yet the same thing as a
native vLLM offload backend.

### 2. Current-stack P-D disaggregation direction

```text
 Prefill node (current stack)           Decode node (current stack)
 +---------------------------+          +---------------------------+
 | vllm_spyre scheduler/     |          | vllm_spyre scheduler/     |
 | worker/model runner       |          | worker/model runner       |
 | + FMS attention/KV        |          | + FMS attention/KV        |
 +-------------+-------------+          +-------------+-------------+
               |                                      ^
               |                                      |
               +---- connector transport / KV push ---+
                         via worker-side bridge
```

This is the direction suggested by:

- current worker-side bridge work in `vllm_spyre`
- upstream vLLM connector / PD-disagg / NIXL work
- the `vllm-spyre` issue about a Spyre KV connector for llm-d and P-D disagg

## KV Reuse / KV Offload / PD Disagg: Next Stack

### 3. Next-stack target shape

```text
            upstream scheduler / connector / HMA / PD logic
                               |
                               v
                 +-------------------------------+
                 | vllm_spyre_next worker/model  |
                 | runner on torch-spyre         |
                 +-------------------------------+
                               |
                               v
                upstream model code + Spyre attn backend
                               |
                               v
                     torch-spyre device tensors
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
           local offload medium         P-D disagg transport
           (host / future medium)       (prefill <-> decode)
```

Why this matters:

- the same upstream connector family could potentially cover both local
  offload and P-D disaggregation
- but that only becomes realistic once the next stack can run paged attention
  and KV-carrying vLLM model code natively on torch-spyre

## Transition Map

```text
                    WHAT WE CAN PROVE FIRST

  Track A: current stack / current compiler stack
  ----------------------------------------------
  prove connector correctness and AIU benefit now
      |
      +--> in-memory reuse on AIU
      +--> current-stack offload experiments
      +--> current-stack P-D disagg experiments


  Track B: next stack / current-to-future compiler transition
  -----------------------------------------------------------
  reduce plugin footprint and move onto torch-spyre substrate
      |
      +--> CPU/dev-test readiness
      +--> wrapped layers + attention backend
      +--> upstream test harness
      +--> torch-spyre device/runtime/compiler prerequisites
      +--> AIU bring-up on next stack


  Convergence
  -----------
  once next stack has:
    - upstream model execution
    - paged attention backend
    - device tensors + copy/stream support
    - distributed / multi-Spyre support
    - enough compiler/runtime maturity

  then KV offload / P-D disagg should migrate toward the next stack and rely
  more directly on upstream vLLM connector abstractions.
```

## What We Have Actually Tested

### Local / CPU

For the current KV-reuse prototype:

- focused connector tests pass locally
- worker-side integration tests pass locally
- offline probe / benchmark harnesses exist and run locally
- local validation proves connector logic and regression safety, but not real
  transport or AIU performance

For `vllm_spyre_next`:

- the public work is currently still mostly at CPU/dev-test readiness and
  layer-by-layer enablement
- there is not yet a full AIU-backed end-to-end KV offload path on the next
  stack

### AIU: current stack

Hardware-backed validation already completed for the current prototype path:

- exact-prefix reuse validated on AIU
- partial-prefix reuse validated on AIU
- zero-miss aligned block loads validated on AIU
- request-latency improvements measured in the single-process offline path

Observed benchmark result from the AIU-backed offline benchmark:

- exact replay: about `1.205x` speedup, about `17.0%` lower request latency
- partial replay: about `1.179x` speedup, about `15.2%` lower request latency

Important caveat:

- this is still a single-process offline path using the current stack
- it proves reuse benefit, not yet full serving-path TTFT or multi-node P-D
  behavior
- these measurements were gathered before the recent repo sync work on the
  vLLM dependency, so they should be treated as a pre-sync AIU baseline and
  re-run on the target pinned environment before becoming the standing
  reference point

### AIU: next stack

Not yet validated for end-to-end KV offload / PD-disagg scenarios.

The public `Spyre-Next` workstream still appears to be in the phase of:

- CPU/dev-test readiness
- wrapped layer bring-up
- custom attention backend scaffolding
- compatibility with newer vLLM versions
- upstream test harness / filtering

## Near-Term Validation Order

### Phase 1: continue with current stack on AIU

This is the right place to keep proving value right now because the seam
already exists and hardware validation is already working.

Recommended order:

1. keep broadening the current AIU benchmark matrix
2. add clearer scheduler-side observability
3. move from offline latency into serving-path / TTFT-oriented measurement
4. test the next transport-backed step on the current stack if needed

### Phase 2: keep next stack moving, but do not force offload onto it too early

The next stack should be treated as the long-term convergence target, but not
as the place to prove the first AIU offload win.

Recommended order:

1. continue layer and attention backend enablement
2. keep syncing to current upstream vLLM
3. keep expanding upstream-test coverage
4. explicitly track multi-Spyre, streams, copy, and compiler/runtime
   prerequisites
5. only move KV offload / P-D disagg experiments there once the basic serving
   path is credible

## Multi-Spyre Deep Dive

### Why multi-Spyre matters here

Multi-Spyre is not only about tensor parallel inference. It matters because it
is the shared foundation for:

- tensor parallel model execution on the next stack
- realistic decode-node scaling in P-D disaggregation
- collective operations used by vLLM model execution
- eventually, more advanced transport and topology-aware data movement

### Current stack vs next stack

```text
 current stack multi-Spyre
 -------------------------
 vllm_spyre + current runtime already has TP-oriented operational paths
 and topology-aware pod scheduling guidance

 next stack multi-Spyre
 ----------------------
 must be built on torch-spyre's native distributed/runtime substrate:
   - distributed backend
   - stream support
   - efficient copy path
   - device-aware compiler/runtime artifacts
```

### Relevant torch-spyre work

- `RFC 0099 / PR #816`
  - multi-Spyre distributed backend via `spyreccl`
  - explicit `torch.distributed` backend story for Spyre
  - directly relevant for next-stack TP and collective support

- `PR #918`
  - stream support for torch-spyre
  - relevant for overlap, async operations, and future copy/collective work

- `PR #1007`
  - graph-free copy via runtime `copyAsync`
  - directly relevant to any serious offload/transport story on the next stack

- `RFC 0248`
  - `SuperDSC-Bundle` frontend/backend contract
  - important for understanding the current compiler-stack boundary

- `RFC / issue 277` and `PR #1010`
  - `SpyreCode` / `JobPlan`
  - important because future runtime execution, copies, and correction steps
    are modeled explicitly there

- `issue 682`
  - `KTIR`
  - signals the future compiler contract replacing `SuperDSC-Bundle`

- `issue 601` and `PR #1049`
  - profiling toolkit, Kineto PrivateUse1 integration, FFDC, HTA direction
  - useful because once the next stack becomes real, debugging and profiling
    offload / PD / multi-card behavior will depend on this tooling

### PyTorch upstream context

- `pytorch/pytorch#172154`
  - `privateuse1` backend integration with Kineto
  - directly supports torch-spyre profiling integration

- `pytorch/pytorch#176877`
  - distributed support for OpenReg
  - the best public reference today for how an out-of-tree accelerator backend
    can integrate with `torch.distributed` in a maintainable way

- `pytorch/pytorch#175954`
  - decomposition-table RFC
  - relevant because out-of-tree backends like torch-spyre need stable ways to
    customize Inductor behavior without fragile monkey-patching

- PyTorch dev-discuss:
  `IBM Spyre Accelerator: PyTorch Enabling Status and Feature Plan - 1H 2026`
  - strongest public roadmap statement for the next stack and torch-spyre
    substrate
  - especially important because it makes the multi-card plan concrete:
    compiled functional collectives first, `torch.distributed` migration
    second, and eventual `torch.comms` alignment later
  - also sharpens the 1H 2026 priorities around single-card production
    inference, attention/backend work, profiling, and vLLM integration

### Practical interpretation

For the immediate KV-offload roadmap:

- multi-Spyre is not the first proof point
- but it is a prerequisite for the serious next-stack future
- so it should be tracked as a first-class dependency, not a side topic
- the March 2026 PyTorch roadmap thread makes this more explicit: multi-card
  support is a staged enablement effort on top of the PyTorch-native path, not
  something that will appear "for free" once the next stack can serve on one
  card

## Public Work To Watch

### vllm-spyre

- issue `#639` `[RFC] vllm-spyre-next`
- issue `#745` `[Epic] Develop KVCacheConnector for Spyre`
- issue `#648` paged KV-cache attention backend using torch-spyre
- issue `#647` contiguous KV-cache attention backend using torch-spyre
- issue `#689` layer-wise split execution in torch-spyre
- issue `#666` run vLLM modeling code instead of FMS modeling code
- PR `#798` custom attention backend for `Spyre-Next`
- PR `#826` update vLLM and torch-spyre for `Spyre-Next`
- PR `#836` wrapped embedding layer for `Spyre-Next`
- PR `#837` upstream tests framework and RMSNorm tests for `Spyre-Next`

### upstream vLLM

- PR `#35264` KV push from prefill to decode node using NIXL connector
- PR `#35760` PD-disagg + speculative decoding acceptance tests
- PR `#36687` support hybrid SSM-FA models in PD disaggregation
- PR `#36957` heterogeneous TP in hybrid-model PD disaggregation
- issue `#36780` RFC for hybrid SSM-FA NIXL connector support
- PR `#37160` simple general CPU KV cache offloading
- PRs `#36642`, `#36644`, `#36645`, `#35223`, `#36549`
  - HMA / multi-group / sliding-window / recovery / multi-connector plumbing

### torch-spyre

- PR `#816` multi-Spyre device support framework
- PR `#918` stream support
- PR `#1007` graph-free copy
- PR `#1049` profiling toolkit RFC
- PR `#1010` SpyreCode / JobPlan alignment
- PR `#1011` tensor memory access analysis
- PR `#868` SuperDSC-Bundle specification
- issue `#682` KTIR
- issue `#183` eager codegen through torch.compile
- issue `#200` new allocator for VF mode

## Priorities

### Highest priority now

1. keep proving KV reuse / offload value on AIU with the current stack
2. keep refining the benchmark and observability story
3. keep tracking upstream connector / PD-disagg / HMA work in vLLM

### Strategic priority

1. track `Spyre-Next` as the long-term landing zone
2. track torch-spyre multi-Spyre / stream / copy / compiler-runtime work as
   explicit prerequisites
3. do not force the next stack to carry offload too early just because it is
   the more elegant end state

### Discussion items for next review

- Which current-stack AIU validations are still missing before transport work?
- What is the minimum next-stack milestone that makes KV-offload experiments
  reasonable there?
- Which upstream vLLM connector / PD-disagg changes are most important to
  mirror in our local design language?
- How much of the current AIU benchmark story should be re-run after each
  major vLLM / torch-spyre version bump?
