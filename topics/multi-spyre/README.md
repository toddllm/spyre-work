# Multi-Spyre

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the umbrella topic for multi-Spyre support in the Spyre +
vLLM story.

It is the best starting point when the question is:

- what does multi-device support actually require?
- why does it matter differently for the current `vllm_spyre` path and
  `vllm-spyre-next`?
- how does it interact with offload and disaggregation?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [Prefill/Decode Disaggregation](../prefill-decode-disaggregation/README.md)
- Neighbor topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- Neighbor topic: [Validation and Proof Plan](../validation-and-proof-plan/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- what not to block near-term single-card proof work on
- which multi-device concerns are still worth naming early

### `vllm-spyre-next` engineers

This topic should answer:

- why scale-out matters much more for the long-term `vllm-spyre-next` story
- what `vllm-spyre-next` goals implicitly assume multi-device maturity

### `torch-spyre` engineers

This topic should answer:

- which capability rungs matter most next: copy, stream, collective, or
  distributed integration
- what higher layers are waiting on

### PyTorch / distributed engineers

This topic should answer:

- where Spyre’s multi-device needs line up with broader out-of-tree accelerator
  backend concerns
- which distributed asks are generally reusable

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### Why is multi-device support its own topic?

Because "more than one card" is not one capability. It is a stack of
capabilities:

- addressing multiple devices
- moving tensors between them
- coordinating execution
- expressing collectives
- integrating with distributed software layers

If any lower rung is weak, higher-level features become difficult or fragile.

</details>

## Generic Dependency Ladder

```text
  multi-device visibility
      ->
  copy paths
      ->
  streams / async coordination
      ->
  collectives
      ->
  distributed backend integration
      ->
  real multi-device inference / serving
```

## Why This Matters To The Bigger Story

Multi-Spyre matters differently by topic:

```text
  KV reuse
    -> not required for the first proof

  KV offload
    -> helpful later, but not first

  P/D disaggregation
    -> much more central

  `vllm-spyre-next`
    -> significantly more important
```

## Current Path vs New Stack

```text
  CURRENT VLLM-SPYRE PATH                VLLM-SPYRE-NEXT TARGET
  ----------------------------------     ----------------------------------
  can prove single-card AIU value        likely long-term home for scale-out
  less dependent on distributed maturity more dependent on distributed maturity
  narrower near-term scope               broader long-term ambitions
```

## Multi-Spyre Capability Map

```text
                    MULTI-SPYRE CAPABILITY MAP

  device discovery / rank mapping
              |
              v
        copy semantics
              |
              v
        stream semantics
              |
              v
      collective semantics
              |
              v
   distributed backend integration
              |
              v
  topology-aware serving / disaggregation / TP
```

## Why This Connects Strongly To P/D Disaggregation

Because once producer and consumer execution contexts stop being purely local,
the design quickly becomes a question of:

- placement
- topology
- transfer paths
- coordination

Those are all multi-device or distributed questions.

## Current Direction

Practical direction under this topic:

- do not make multi-Spyre a prerequisite for proving basic AIU value
- do treat it as a core dependency for the `vllm-spyre-next` long-term
  direction
- keep tracking stream/copy/collective/distributed milestones closely

## Communication Goal

The main communication job of this topic is to keep multi-Spyre from being
either ignored as "later" or overloaded as an immediate prerequisite for every
current topic. It needs to stay visible in the right proportion.

## Related Source-Repos and References

- Multi-Spyre device support framework:
  [torch-spyre PR #816](https://github.com/torch-spyre/torch-spyre/pull/816)
- Multi-device support investigation:
  [torch-spyre issue #99](https://github.com/torch-spyre/torch-spyre/issues/99)
- Stream support:
  [torch-spyre PR #918](https://github.com/torch-spyre/torch-spyre/pull/918)
- Graph-free copy:
  [torch-spyre PR #1007](https://github.com/torch-spyre/torch-spyre/pull/1007)
- New allocator investigation:
  [torch-spyre issue #200](https://github.com/torch-spyre/torch-spyre/issues/200)
- PyTorch dev-discuss roadmap:
  [1H 2026 Spyre roadmap thread](https://dev-discuss.pytorch.org/t/ibm-spyre-accelerator-pytorch-enabling-status-and-feature-plan-1h-2026/3319)
- OpenReg distributed support context:
  [pytorch/pytorch #176877](https://github.com/pytorch/pytorch/issues/176877)
