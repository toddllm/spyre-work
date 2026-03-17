# Prefill/Decode Disaggregation

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the top-level map for prefill/decode disaggregation in the
Spyre + vLLM context.

It starts from first principles and then narrows to the concrete Spyre
mechanisms that matter most right now, especially KV transfer between producer
and consumer execution contexts.

This topic is intentionally broader than:

- one transfer transport
- one PD connector implementation
- one topology layout

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Tactical watch list: [../../LIVE_TRACKER.md](../../LIVE_TRACKER.md)
- Neighbor topic: [KV Reuse](../kv-reuse/README.md)
- Neighbor topic: [KV Offload](../kv-offload/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- whether a narrow current path P/D-style experiment is worth doing
- what translation burden that experiment would inherit

### `vllm-spyre-next` engineers

This topic should answer:

- why P/D disaggregation is a longer-term destination
- what `vllm-spyre-next` maturity should exist before it becomes a real target

### Upstream vLLM engineers

This topic should answer:

- how Spyre wants to relate to upstream NIXL / PD-disagg semantics
- what is meant to stay common with offload semantics

### `torch-spyre` and multi-device engineers

This topic should answer:

- where transport, copy, topology, and distributed maturity start to dominate
- why disaggregation is not just a connector problem

</details>

<details markdown="1">
<summary><strong>Scope</strong></summary>


This note is intentionally layered:

1. Prefill/decode disaggregation in general
2. KV transfer as the enabling mechanism
3. Current Spyre software stack
4. `vllm-spyre-next` / new stack
5. Current proof direction and dependencies

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What problem is being solved?

Prefill and decode have materially different runtime shapes.

Prefill/decode disaggregation means these phases do not have to live in the
same execution context.

In a disaggregated design:

- one context produces prompt KV during prefill
- that KV is handed off with enough metadata to trust it
- another context consumes it and continues decode

### Why is this attractive?

Because it can support:

- specialization by phase
- different placement decisions for prefill and decode
- better resource utilization
- broader serving architectures

### How is this different from KV offload?

Offload:

- same logical serving context
- save / reload oriented

Prefill/decode disaggregation:

- distinct producer and consumer contexts
- handoff / transfer oriented

### What stays common with offload and reuse?

All three still need:

- prefix identity
- block identity
- representation mapping
- lifecycle completion semantics
- error handling

</details>

## Minimal Disaggregation Contract

Any serious P/D disaggregation design needs answers to:

```text
  1. Who produces the KV?
  2. Who consumes the KV?
  3. What transfer unit is authoritative?
  4. When is handoff complete enough for decode to trust?
  5. What happens on partial transfer, stale metadata, or failure?
```

### State That Must Be Tracked

```text
  producer identity
  consumer identity
  prefix / request identity
  logical block ids
  transfer representation
  transfer completion state
  decode-ready boundary
  retry / invalidation / recovery state
```

## Generic Disaggregation Model

```text
                GENERIC PREFILL/DECODE DISAGGREGATION

  Prefill context
      |
      +--> compute prompt KV
      +--> package metadata + transfer units
      +--> transfer to decode context
      |
      v
  Decode context
      |
      +--> validate transfer
      +--> map into execution representation
      +--> continue decode iterations
      |
      v
  request result
```

## Generic Transfer and Mapping Model

```text
                TRANSFER + MAPPING + TRUST MODEL

  producer-side live KV
          |
          v
  producer export representation
          |
          v
  transport / handoff medium
          |
          v
  consumer import representation
          |
          v
  consumer-side live KV
          |
          v
  decode continuation
```

The main design question is how much translation exists at each step.

## Current Spyre Software Stack

The current Spyre software stack does not offer the ideal upstream-native seam
for P/D
disaggregation, but it does expose a real worker/model-runner seam that could
support a narrow proving experiment.

### Current Path P/D Transfer Flow

```text
                CURRENT PATH P/D TRANSFER FLOW

  Prefill side                                 Decode side
  -----------------------------                -----------------------------
  scheduler emits metadata                     scheduler receives metadata
            |                                               ^
            v                                               |
  worker / model runner + bridge                            |
            |                                               |
  staged/live sync around FMS KV                            |
            |                                               |
  save / export from staged view  ---- transport ---->  load into staged view
                                                            |
                                                            v
                                                  staged/live sync into FMS KV
                                                            |
                                                            v
                                                      decode continues
```

### Current Path Representation View

```text
               CURRENT PATH TRANSFER REPRESENTATIONS

  prefill live FMS KV
          |
          | explicit sync
          v
   prefill staged representation
          |
          v
       transport
          |
          v
   decode staged representation
          |
          | explicit sync
          v
   decode live FMS KV
```

### Why the Current Path Is Plausible at All

Because it already has:

- scheduler-visible connector metadata
- bridge lifecycle around forward execution
- explicit staged/live synchronization points

So while awkward, it is a real seam.

### Why the Current Path Is Not the Final Architecture

Because it still carries:

- FMS-owned live KV
- synchronous bridge behavior
- explicit staged/live translation burden
- no mature distributed / topology substrate for this use case

That means current path P/D work should be treated as:

- a narrow proving experiment if needed
- not the target architecture

### Current Code Touchpoints

- [`spyre_kv_connector_bridge.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py)
  - connector lifecycle and load/save/transfer control
- [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/v1/worker/spyre_model_runner.py)
  - current synchronization boundary around forward execution
- Spyre connector epic:
  [vllm-spyre issue #745](https://github.com/vllm-project/vllm-spyre/issues/745)

## vllm-spyre-next / New Stack

`vllm-spyre-next` is the natural long-term home for meaningful P/D
disaggregation because it should align more directly with upstream connector
abstractions and with the evolving torch-spyre distributed substrate.

### New Stack P/D Target

```text
             VLLM-SPYRE-NEXT PREFILL/DECODE DISAGGREGATION

    upstream scheduler / connector / PD logic
                     |
           +---------+---------+
           |                   |
           v                   v
     prefill execution    decode execution
     upstream model code  upstream model code
     + Spyre backend      + Spyre backend
           |                   ^
           +----- KV handoff ---+
                through shared connector semantics
```

### Dependency Ladder for Real P/D Disaggregation

```text
  connector-family semantics
      ->
  `vllm-spyre-next` execution maturity
      ->
  paged attention maturity
      ->
  copy / stream maturity
      ->
  multi-Spyre / distributed maturity
      ->
  meaningful P/D disaggregation
```

### Why Multi-Spyre Matters Here More Than in Reuse

Because serious P/D disaggregation quickly becomes a question of:

- placement
- transport
- topology
- distributed ownership

Those questions are much more central here than in basic local reuse.

## Current Path vs New Stack

```text
  CURRENT VLLM-SPYRE PATH                VLLM-SPYRE-NEXT TARGET
  ----------------------------------     ----------------------------------
  narrow bridge-driven experiment        upstream connector-native design
  staged/live transfer burden            cleaner execution ownership
  good for proving one seam              good for real architecture
  weak distributed story                 depends on multi-Spyre maturity
```

## What Must Be Tracked Regardless of Stack

```text
  producer / consumer identity
  request / prefix identity
  block identity
  transfer representation
  transfer completion boundary
  decode-ready boundary
  errors / retries / invalidation
  latency / throughput / placement impact
```

## Current Spyre Direction

Near-term direction under the P/D disaggregation umbrella:

- do not treat this as the first AIU proof target
- settle connector-family semantics first through reuse and offload
- use current path P/D work only if a narrow experiment answers a question
  that reuse/offload cannot answer
- treat `vllm-spyre-next` plus multi-Spyre maturity as the long-term landing
  zone

That proof ladder looks like:

```text
  first principles
      ->
  reuse and offload semantics
      ->
  `vllm-spyre-next` execution maturity
      ->
  multi-Spyre maturity
      ->
  meaningful P/D disaggregation
```

## Communication Goal

The main communication job of this topic is to help teams discuss
disaggregation as a real architecture target without prematurely collapsing it
into either a local offload problem or a purely distributed-systems problem.

## Related Source-Repos and References

- Upstream KV push PR:
  [vLLM PR #35264](https://github.com/vllm-project/vllm/pull/35264)
- P/D acceptance tests:
  [vLLM PR #35760](https://github.com/vllm-project/vllm/pull/35760)
- Hybrid-model PD work:
  [vLLM PR #36687](https://github.com/vllm-project/vllm/pull/36687),
  [#36957](https://github.com/vllm-project/vllm/pull/36957)
- Hybrid-model NIXL RFC issue:
  [vLLM issue #36780](https://github.com/vllm-project/vllm/issues/36780)
- Spyre connector epic:
  [vllm-spyre issue #745](https://github.com/vllm-project/vllm-spyre/issues/745)
- Multi-Spyre device support:
  [torch-spyre PR #816](https://github.com/torch-spyre/torch-spyre/pull/816)
- Stream support:
  [torch-spyre PR #918](https://github.com/torch-spyre/torch-spyre/pull/918)
- Graph-free copy:
  [torch-spyre PR #1007](https://github.com/torch-spyre/torch-spyre/pull/1007)
