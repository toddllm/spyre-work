# KV Offload

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the top-level map for KV offload in the Spyre + vLLM context.

It starts from first principles and then narrows to the concrete Spyre path
that matters most right now: transport-backed local offload.

This topic is intentionally broader than:

- one offload medium
- one connector implementation
- one hardware generation

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Tactical watch list: [../../LIVE_TRACKER.md](../../LIVE_TRACKER.md)
- Neighbor topic: [KV Reuse](../kv-reuse/README.md)
- Neighbor topic: [Prefill/Decode Disaggregation](../prefill-decode-disaggregation/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- where the first real offload seam exists today
- what save/load/copy state has to stay aligned around that seam

### `vllm-spyre-next` engineers

This topic should answer:

- what the long-term offload ownership model should look like
- why `vllm-spyre-next` is the destination rather than the first proof point

### Upstream vLLM engineers

This topic should answer:

- how Spyre wants to align with upstream HMA/offload semantics
- what awkwardness on the current path is temporary versus fundamental

### `torch-spyre` engineers

This topic should answer:

- which copy, medium, and lower-layout guarantees would make offload cleaner
- what transport-backed local offload is really asking of the substrate

</details>

<details markdown="1">
<summary><strong>Scope</strong></summary>


This note is intentionally layered:

1. KV offload in general
2. Offload unit, mapping, medium, and lifecycle
3. Current Spyre software stack
4. `vllm-spyre-next` / new stack
5. Current proof direction

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What problem is being solved?

KV state does not necessarily need to remain resident in the active execution
context at all times.

KV offload means:

- KV is saved to another medium
- active execution may release or avoid retaining all of that KV locally
- later execution reloads the required KV back into the execution context

This is useful when active KV residency becomes a pressure point for:

- capacity
- concurrency
- topology choices
- specialization between execution contexts

### How is KV offload different from KV reuse?

KV reuse is primarily about:

- already having compatible reusable KV for a later request

KV offload is primarily about:

- moving KV out of the active execution context and bringing it back later

They overlap, but they are not the same:

```text
  reuse
    -> trust existing compatible KV

  offload
    -> explicitly save and later reload KV
```

### How is KV offload different from prefill/decode disaggregation?

Offload:

- same logical serving context
- storage / reload oriented

Prefill/decode disaggregation:

- producer and consumer may be different execution contexts
- handoff / transfer oriented

</details>

## Minimal Offload Contract

Any serious KV offload design needs answers to:

```text
  1. What unit gets saved and loaded?
  2. How is it named or addressed?
  3. Where is it stored?
  4. When is save/load considered complete?
  5. What happens on miss, partial load, or failure?
```

### State That Must Be Tracked

```text
  logical block ids
  physical / staged representation
  medium key or address
  save completion state
  load completion state
  capacity / eviction state
  version / freshness
  latency / bytes moved
```

## Generic Offload Model

```text
                        GENERIC KV OFFLOAD MODEL

  active execution context
         |
         +--> choose KV units to save
         |
         +--> map execution representation to offload representation
         |
         +--> save to medium
         |
         +--> release or avoid retaining all active KV
         |
         +--> later reload required units
         |
         +--> remap into execution representation
         |
         v
  continue execution
```

## Current Reporting Snapshot

- [Current-Stack AIU KV Status (2026-03-17)](../validation-and-proof-plan/current-stack-aiu-kv-status-2026-03-17.md)
  - best compact statement of what is proven now versus what remains unproven
  - useful when the question is "where exactly are we on offload today?"

## Generic Mapping Model

```text
                  OFFLOAD MAPPING AND COPYING MODEL

  logical KV blocks
        |
        v
  execution-layout representation
        |
        +--> optional translation / staging boundary
        |
        v
   offload-medium representation
        |
        v
  medium key / address / handle
```

The exact design question is whether these are:

- the same representation
- compatible representations
- or explicitly translated representations

## Current Spyre Software Stack

The current Spyre software stack is the most realistic place to attempt the
first serious AIU offload step because the worker/model-runner seam and
staged/live sync seam already exist.

### Current Path Offload Flow

```text
                 CURRENT PATH TRANSPORT-BACKED OFFLOAD FLOW

  scheduler
      |
      +--> kv_connector_metadata
      |
      v
  Spyre worker / model runner
      |
      +--> bridge.begin_step()
      +--> bridge.before_forward()
      |      - metadata bind
      |      - start load
      |
      +--> staged view -> live FMS KV sync
      |
      +--> FMS forward
      |
      +--> live FMS KV -> staged view sync
      |
      +--> bridge.after_forward()
      |      - save completion
      |      - load completion
      |      - errors / stats
      |
      v
  offload medium
      - host memory first
      - other local media later
```

### Current Path Copying Model

```text
                   CURRENT PATH COPYING MODEL

  reusable / offload store
          |
          v
   staged KV buffers
          |
          | explicit sync
          v
    live FMS KV tensors
          |
          v
      FMS attention
          |
          v
    live FMS KV tensors
          |
          | explicit sync
          v
   staged KV buffers
          |
          v
   offload store
```

### Current Path Tracking Model

```text
                CURRENT PATH STATE THAT MUST STAY ALIGNED

  scheduler metadata
      - block ids
      - prefix accounting
      - request state
               |
               v
  bridge bookkeeping
      - started loads
      - finished loads
      - finished saves
      - errors
      - stats
               |
               v
  staged/live sync boundary
      - which buffers are authoritative?
      - when is sync complete?
      - what can attention trust?
```

### Why the Current Stack Is the First Offload Seam

Because it already contains:

- connector metadata plumbing
- load/save lifecycle hooks
- explicit staged/live translation points
- a place to measure save/load behavior on AIU

The offload seam is not clean, but it is real.

### Current Code Touchpoints

- [`spyre_kv_connector_bridge.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py)
  - connector lifecycle and load/save control
- [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_model_runner.py)
  - staged/live synchronization and forward integration
- [`spyre_worker.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_worker.py)
  - execution entry point
- [`spyre-kv-offload-research.md`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-research.md)
  - current research framing
- [`spyre-kv-offload-rfc-draft.md`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-rfc-draft.md)
  - current proposed roadmap shape

## vllm-spyre-next / New Stack

The `vllm-spyre-next` target should align offload more directly with upstream
connector/offload concepts and less with worker-side translation glue.

### New Stack Offload Target

```text
                 VLLM-SPYRE-NEXT KV OFFLOAD TARGET

   upstream scheduler / connector / offload logic
                    |
                    v
    upstream model execution + Spyre attention backend
                    |
                    v
       torch-spyre-backed tensor / KV substrate
                    |
                    v
                offload medium
```

### What Should Improve on vllm-spyre-next

```text
  current vllm-spyre path
    - worker/model-runner seam owns offload integration
    - staged/live translation is explicit
    - medium semantics inherit that awkwardness

  `vllm-spyre-next` target
    - upstream-aligned offload semantics
    - backend-specific mapping lower in the stack
    - cleaner ownership between scheduler, execution, and medium
```

### Why vllm-spyre-next Is Not the First Offload Proof Point

Because `vllm-spyre-next` still depends on:

- execution maturity
- paged attention maturity
- copy / stream maturity in torch-spyre

That makes it the better destination, not the first proof seam.

## Current Path vs New Stack

```text
  CURRENT VLLM-SPYRE PATH                VLLM-SPYRE-NEXT TARGET
  ----------------------------------     ----------------------------------
  worker/model-runner-centric            upstream connector-centric
  staged/live sync required              cleaner ownership split
  best first AIU seam                    better long-term architecture
  translation burden visible             translation burden pushed lower
```

## What Must Be Tracked Regardless of Stack

```text
  save unit
  load unit
  logical -> physical mapping
  medium addressing
  freshness / version
  bytes moved
  save/load latency
  miss / failure / retry
  capacity / eviction accounting
```

## Current Spyre Direction

Near-term direction under the KV offload umbrella:

- keep the first meaningful offload experiment on the current `vllm_spyre`
  path
- use a deliberately modest medium and contract first
- optimize for observability and clean semantics before sophistication
- use the result to shape how `vllm-spyre-next` should align with upstream
  HMA / offload language

That proof ladder looks like:

```text
  first principles
      ->
  local KV reuse proof
      ->
  transport-backed local offload on the current vllm-spyre path
      ->
  `vllm-spyre-next` offload alignment
```

## Communication Goal

The main communication job of this topic is to separate offload semantics from
today’s translation mechanics on the current path while still being concrete
enough
for people working on the first AIU offload seam.

## Related Source-Repos and References

- General upstream offload direction:
  [vLLM PR #37160](https://github.com/vllm-project/vllm/pull/37160)
- Connector composition / HMA plumbing:
  [vLLM PR #36549](https://github.com/vllm-project/vllm/pull/36549),
  [#36642](https://github.com/vllm-project/vllm/pull/36642),
  [#36644](https://github.com/vllm-project/vllm/pull/36644),
  [#36645](https://github.com/vllm-project/vllm/pull/36645)
- Scheduler-side HMA recovery:
  [vLLM PR #35223](https://github.com/vllm-project/vllm/pull/35223)
- Spyre connector epic:
  [vllm-spyre issue #745](https://github.com/vllm-project/vllm-spyre/issues/745)
- `vllm-spyre-next` rationale:
  [vllm-spyre issue #639](https://github.com/vllm-project/vllm-spyre/issues/639)
