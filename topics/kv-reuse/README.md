# KV Reuse

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the top-level map for KV reuse in the Spyre + vLLM context.

It starts from first principles and then narrows all the way down to the
current Spyre implementation seams, the `vllm-spyre-next` target shape, and
the proof sequence that matters most right now.

This topic is intentionally broader than:

- one implementation branch
- one connector prototype
- one benchmark result

At the moment, the concrete Spyre focus under this umbrella is local KV reuse.

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Tactical watch list: [../../LIVE_TRACKER.md](../../LIVE_TRACKER.md)
- Neighbor topic: [KV Offload](../kv-offload/README.md)
- Neighbor topic: [Prefill/Decode Disaggregation](../prefill-decode-disaggregation/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- where local reuse attaches today
- what state is authoritative across scheduler, bridge, and live execution

### `vllm-spyre-next` engineers

This topic should answer:

- what ownership should migrate later
- what parts of the current reuse seam are temporary proof machinery

### Upstream vLLM engineers

This topic should answer:

- which reuse semantics Spyre should align with upstream
- where backend-specific translation still exists today

### `torch-spyre` engineers

This topic should answer:

- which tensor/copy/layout assumptions higher layers are implicitly making
- what should remain abstract at this layer versus become an explicit substrate
  contract

</details>

<details markdown="1">
<summary><strong>Scope</strong></summary>


This note is intentionally layered:

1. KV reuse in general
2. Reuse identity, lifecycle, and ownership
3. Current Spyre software stack
4. `vllm-spyre-next` / new stack
5. Current proof status and next proof steps

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What problem is being solved?

A decoder model builds key/value state for prompt tokens. If a later request
shares a prefix that is genuinely reusable, recomputing that prefix is wasted
work.

KV reuse means:

- a request computes KV state
- some portion of that KV state becomes reusable
- a later request loads and trusts that KV state instead of rebuilding it

### Why is this valuable?

Because repeated-prefix traffic shifts work from:

```text
  prompt tokens
      ->
  attention + KV build
      ->
  continue request
```

to:

```text
  prompt tokens
      ->
  identify reusable prefix
      ->
  load matching KV state
      ->
  continue request
```

When prompt-side work is large enough, this can materially reduce request
latency and prompt compute.

### Why is KV reuse not just "cache some tensors"?

Because correctness depends on several things staying aligned at once:

- prefix identity
- block identity
- layout compatibility
- scheduler-visible consumed-token accounting
- model-runner-visible execution starting point

KV reuse is really the intersection of:

- identity
- mapping
- ownership
- lifecycle
- observability

</details>

## The Minimal Reuse Contract

At minimum, any KV reuse design needs a consistent answer to:

```text
  1. What prefix is reusable?
  2. What unit of KV is being reused?
  3. Where is that KV stored?
  4. Who says it is safe to trust?
  5. How does execution resume from the reuse boundary?
```

### Reuse Unit

In practice the reuse unit is usually some variant of:

- logical KV blocks
- per-layer block slices
- a backend-specific staging representation derived from logical blocks

### Reuse Lifecycle

```text
  request arrives
      ->
  scheduler binds reuse metadata
      ->
  execution context loads reusable KV
      ->
  remaining prompt / decode work runs
      ->
  newly reusable KV may be saved
      ->
  request finishes
```

### State That Must Stay Consistent

```text
  reusable prefix length
  block ids / block order
  per-layer KV slices
  backend layout / tensor shape
  scheduler-visible consumed work
  model-runner-visible resume point
  success / miss / failure accounting
```

## Generic KV Reuse Model

```text
                      GENERIC KV REUSE MODEL

  Request N
     |
     +--> hash / match reusable prefix
     |
     +--> resolve reusable KV units
     |
     +--> map logical units to execution layout
     |
     +--> load reusable KV into execution context
     |
     +--> resume execution after the reuse boundary
     |
     +--> optionally save newly reusable KV units
     |
     v
   Request result
```

## Generic Ownership Model

```text
                  WHO OWNS WHAT IN KV REUSE?

  scheduler / request state
      - prefix identity
      - consumed-token accounting
      - block metadata
                 |
                 v
  connector / store
      - persistent or semi-persistent reusable units
      - save/load completion
      - misses / failures / stats
                 |
                 v
  execution context
      - execution-layout mapping
      - live tensors used by attention
      - resume point correctness
```

## Current Spyre Stack

The current Spyre software stack is roughly:

```text
  user / API / LLM.generate
            |
            v
     upstream vLLM engine
            |
            v
      vllm_spyre plugin
      - custom scheduler
      - custom worker
      - custom model runner
            |
            v
      FMS model code
      FMS attention path
            |
            v
      sendnn / current runtime
            |
            v
           AIU
```

On this stack, KV reuse attaches at the worker/model-runner seam, not at a
clean upstream model-native seam.

### Current Path Reuse Flow

```text
                     CURRENT PATH KV REUSE FLOW

  scheduler
     |
     +--> kv_connector_metadata
     |
     v
  Spyre worker / model runner
     |
     +--> bridge.begin_step()
     +--> bridge.before_forward()
     |      - bind connector metadata
     |      - start KV load
     |
     +--> sync_loaded_kv_from_staging()
     |      - staged view -> live FMS KV
     |
     +--> FMS forward
     |      - live KV mutated here
     |
     +--> sync_fms_kv_to_staging()
     |      - live FMS KV -> staged view
     |
     +--> bridge.after_forward()
     |      - save completion
     |      - recv/send completion
     |      - errors
     |      - stats
     |
     +--> bridge.finish_step()
     |
     v
  reusable KV store
     - in-memory today
```

### Current Path Data Representations

The central fact about the current path is that there are two different KV
representations in play:

```text
   logical scheduler-visible KV blocks
                  |
                  v
       connector-side staged KV representation
                  |
       explicit sync / translation boundary
                  |
                  v
            live FMS KV tensors
                  |
                  v
            FMS attention execution
```

That translation boundary is why the current seam is both useful and awkward.

### Current Path Detailed Mapping View

```text
                  CURRENT PATH REUSE MAPPING VIEW

  request + prefix metadata
            |
            v
     scheduler-visible block ids
            |
            v
   connector metadata / block lookup
            |
            v
   staged KV buffers in bridge-owned view
            |
            +--> load complete?
            +--> load errors?
            +--> block count?
            |
            v
   sync into live FMS KV tensors
            |
            v
   attention uses live FMS KV
            |
            v
   sync newly-produced KV back to staged view
            |
            v
   staged save back to reusable store
```

### What the Current Stack Already Proves

Current work has already shown:

- exact reuse can work
- partial-prefix reuse can work
- block-aligned reuse can work
- worker-side save/load accounting can work
- AIU-backed offline latency can improve

What it has not yet settled:

- serving-path TTFT benefit
- transport-backed offload behavior
- the final ownership shape for `vllm-spyre-next`

### Current Code Touchpoints

- [`spyre_kv_connector_bridge.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py)
  - bridge lifecycle and connector handshake
- [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_model_runner.py)
  - bridge wiring around forward execution and staged/live synchronization
- [`spyre_worker.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/v1/worker/spyre_worker.py)
  - worker entry point and execution delegation
- [`spyre.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/model_executor/model_loader/spyre.py)
  - current path model loading, compile path, and attention/KV setup

## vllm-spyre-next / New Stack

The `vllm-spyre-next` target is closer to:

```text
  user / API / LLM.generate
            |
            v
     upstream vLLM engine
            |
            v
      thinner Spyre plugin
            |
            v
   upstream model code + Spyre attention backend
            |
            v
      torch-spyre substrate
            |
            v
           AIU
```

On that stack, KV reuse should ideally align more directly with upstream
connector semantics and less with worker-side staged/live translation glue.

### New Stack Reuse Target

```text
               VLLM-SPYRE-NEXT KV REUSE TARGET

   upstream scheduler / connector logic
                 |
                 v
   upstream model execution + Spyre backend
                 |
                 v
      torch-spyre-backed tensor / KV substrate
                 |
                 v
           reusable KV store
```

### What Should Change on vllm-spyre-next

```text
  current vllm-spyre path
    - FMS owns live KV
    - bridge synchronizes staged <-> live views
    - reuse seam is worker/model-runner-centric

  `vllm-spyre-next` target
    - upstream model execution owns the main execution flow
    - reuse semantics should look more like upstream connector semantics
    - backend-specific mapping should be lower in the stack
```

### Why vllm-spyre-next Is Not the First Proof Point

Because `vllm-spyre-next` KV reuse depends on:

- `vllm-spyre-next` execution maturity
- paged attention maturity
- tensor/copy maturity in torch-spyre

That makes it a better long-term landing zone than a first hardware proof seam.

## Current Path vs New Stack

```text
  CURRENT VLLM-SPYRE PATH                VLLM-SPYRE-NEXT TARGET
  ----------------------------------     ----------------------------------
  worker/model-runner seam               model/backend-aligned seam
  staged <-> live translation            less explicit staging glue
  FMS-owned live KV                      upstream-owned execution flow
  best proof seam now                    better long-term destination
```

## What Must Be Tracked Regardless of Stack

```text
  prefix identity
  logical block identity
  execution-layout mapping
  load/save completion
  misses / partial hits
  errors / stale metadata
  consumed-token accounting
  latency / throughput impact
```

## Current Spyre Direction

Near-term direction under the KV reuse umbrella:

- keep proving value on the current `vllm_spyre` path
- strengthen observability
- move from offline latency wins to serving-path evidence
- use those results to inform the `vllm-spyre-next` ownership model

That proof ladder looks like:

```text
  first principles
      ->
  current path local KV reuse
      ->
  stronger AIU validation
      ->
  `vllm-spyre-next` KV reuse design
```

## Communication Goal

The main communication job of this topic is to let different teams talk about
the same reuse problem without confusing logical reuse semantics, translation
mechanics on the current path, and the long-term `vllm-spyre-next` ownership
target.

## Related Source-Repos and References

- Working research draft:
  [spyre-kv-offload-research.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-research.md)
- Working RFC draft:
  [spyre-kv-offload-rfc-draft.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-rfc-draft.md)
- Spyre connector epic:
  [vllm-spyre issue #745](https://github.com/vllm-project/vllm-spyre/issues/745)
- `vllm-spyre-next` rationale:
  [vllm-spyre issue #639](https://github.com/vllm-project/vllm-spyre/issues/639)
- Upstream general KV offload direction:
  [vLLM PR #37160](https://github.com/vllm-project/vllm/pull/37160)
