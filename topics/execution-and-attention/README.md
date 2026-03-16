# Execution and Attention

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the umbrella topic for execution flow and attention ownership
in the Spyre + vLLM context.

It is the best starting point when the question is:

- where does token execution actually happen?
- who owns live KV state?
- how does attention differ between the current `vllm_spyre` path and
  `vllm-spyre-next`?
- what has to mature before advanced KV features belong on
  `vllm-spyre-next`?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [Current Path and vllm-spyre-next](../current-vs-next-stack/README.md)
- Neighbor topic: [KV Reuse](../kv-reuse/README.md)
- Neighbor topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- where live KV is actually owned today
- why the current bridge/model-runner seam exists

### `vllm-spyre-next` engineers

This topic should answer:

- what execution/attention maturity still needs to land
- what advanced KV features should wait until that maturity exists

### Upstream vLLM engineers

This topic should answer:

- which parts of execution should remain upstream-owned in the long run
- where Spyre currently has backend-specific execution baggage

### `torch-spyre` engineers

This topic should answer:

- which lower substrate capabilities the attention/backend story depends on
- how much execution complexity is being pushed downward

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### Why is execution/attention a separate topic?

Because KV reuse, offload, and disaggregation all eventually depend on the
same deep question:

```text
  who owns the live execution state that attention actually consumes?
```

If that ownership is awkward, every higher-level KV feature becomes awkward.

### What needs to line up?

```text
  scheduler-visible request state
      ->
  model-runner-visible execution state
      ->
  attention-visible live KV state
      ->
  compiler/runtime-visible tensor state
```

</details>

## Generic Execution Model

```text
                 GENERIC EXECUTION + ATTENTION MODEL

  request metadata
        |
        v
  scheduler / batching
        |
        v
  model execution wrapper
        |
        v
  attention implementation
        |
        v
  live KV state used during execution
        |
        v
  prompt / decode continuation
```

## Current Spyre Software Stack

In the current Spyre software stack, execution and attention are centered on
FMS model code.

```text
  upstream vLLM engine
         |
         v
    vllm_spyre
    - scheduler
    - worker
    - model runner
         |
         v
    FMS model code
    FMS attention / live KV
         |
         v
    sendnn / current runtime
         |
         v
        AIU
```

### Current Path Execution Ownership

```text
  scheduler decides work
      ->
  model runner prepares execution
      ->
  bridge may load/save staged KV
      ->
  FMS attention consumes live FMS KV
      ->
  model runner syncs live KV back to staged view if needed
```

### Why this matters

Because the live KV that attention trusts is not just a generic upstream vLLM
representation. It is bound to the current FMS execution path.

## vllm-spyre-next / New Stack

The `vllm-spyre-next` target is to move execution closer to upstream vLLM
model code with a Spyre-specific attention/backend layer.

```text
  upstream vLLM engine
         |
         v
    vllm-spyre-next
         |
         v
  upstream model code
  + Spyre attention backend
         |
         v
    torch-spyre substrate
         |
         v
        AIU
```

### New Stack Execution Ownership

```text
  scheduler decides work
      ->
  upstream model execution drives the flow
      ->
  Spyre backend implements attention / KV access
      ->
  torch-spyre substrate owns lower tensor/runtime behavior
```

## Current vs Next: Attention Ownership

```text
  CURRENT VLLM-SPYRE PATH                VLLM-SPYRE-NEXT TARGET
  ----------------------------------     ----------------------------------
  FMS attention owns live KV             Spyre backend under upstream flow
  model runner wraps execution           thinner wrapper around execution
  bridge translates staged/live views    less translation at plugin layer
  good proof seam today                  better long-term architecture
```

## Why This Topic Controls the Others

```text
  execution + attention maturity
      ->
  KV reuse shape
      ->
  KV offload shape
      ->
  P/D disaggregation credibility
```

If execution maturity is weak, higher-level KV features either become awkward
or get forced into the wrong seam too early.

## Code and Implementation References

- `vllm-spyre-next` attention backend work:
  [vllm-spyre issue #647](https://github.com/vllm-project/vllm-spyre/issues/647)
  and [#648](https://github.com/vllm-project/vllm-spyre/issues/648)
- Integrated custom attention backend:
  [vllm-spyre PR #798](https://github.com/vllm-project/vllm-spyre/pull/798)
- Upstream model-code transition:
  [vllm-spyre issue #666](https://github.com/vllm-project/vllm-spyre/issues/666)
- Layer-wise split execution:
  [vllm-spyre issue #689](https://github.com/vllm-project/vllm-spyre/issues/689)
- Current model loader path in working fork:
  [`spyre.py`](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/vllm_spyre/model_executor/model_loader/spyre.py)

## Current Direction

Near-term direction under this topic:

- keep advanced KV work grounded on the current `vllm_spyre` path where
  execution is known
- keep pushing `vllm-spyre-next` execution and attention maturity
- use `vllm-spyre-next` execution readiness as a gating condition for when
  offload and disaggregation should migrate there

## Communication Goal

The main communication job of this topic is to keep everyone honest about the
fact that KV features ultimately depend on who owns live execution state and
attention behavior. If that stays fuzzy, every cross-team conversation about
reuse, offload, or disaggregation gets harder.
