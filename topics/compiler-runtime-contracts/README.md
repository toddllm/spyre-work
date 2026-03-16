# Compiler/Runtime Contracts

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the umbrella topic for the compiler/runtime contract layer in
the Spyre + vLLM story.

It is the best starting point when the question is:

- what assumptions does the plugin make about the underlying runtime?
- what is changing underneath torch-spyre?
- how should that affect stack design and feature planning?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [Current Path and vllm-spyre-next](../current-vs-next-stack/README.md)
- Neighbor topic: [Execution and Attention](../execution-and-attention/README.md)
- Neighbor topic: [Multi-Spyre](../multi-spyre/README.md)
- Deeper topic: [SuperDSC and Current Contracts](../superdsc-and-current-contracts/README.md)
- Deeper topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- Deeper topic: [KTIR and Future IR](../ktir-and-future-ir/README.md)

</details>

<details markdown="1">
<summary><strong>Topic Map</strong></summary>


This umbrella is easier to navigate as three separate low-level topics.

### [SuperDSC and Current Contracts](../superdsc-and-current-contracts/README.md)

Use this when the conversation is about the current contract family that the
current AIU path actually runs through, including where `sdsc.json`,
`g2.graph.cbor`, `sendnn`, and the runtime fit together.

### [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)

Use this when the conversation is about the broader torch-spyre backend/device
direction behind the rough `backend="inductor"` framing, including the device,
allocator, layout, wrapper, and pass machinery that higher layers will depend
on.

### [KTIR and Future IR](../ktir-and-future-ir/README.md)

Use this when the conversation is specifically about future IR or artifact
questions. KTIR is one public thread inside the future compiler/backend
direction, but it is not the whole definition of that direction.

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- which lower-level assumptions are safe to rely on today
- which assumptions are moving targets and should not leak into long-lived
  architecture claims

### `vllm-spyre-next` engineers

This topic should answer:

- which substrate milestones actually gate `vllm-spyre-next` ambitions
- which changes are contract churn versus meaningful platform improvement

### `torch-spyre` engineers

This topic should answer:

- what higher layers need the substrate to promise
- what language higher layers are using for unstable versus stable assumptions

### PyTorch / distributed engineers

This topic should answer:

- where Spyre’s needs map onto broader PyTorch backend and distributed hooks
- which asks are backend-specific versus generally useful

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### Why are compiler/runtime contracts a separate topic?

Because a serving plugin depends not just on model semantics but on what the
underlying device stack can promise.

That contract includes:

- tensor layout assumptions
- copy semantics
- compilation entry points
- runtime artifact format
- execution submission model

If that contract changes, the plugin and backend assumptions above it may need
to change too.

</details>

## Generic Contract Layer Model

```text
  serving / model layer
        |
        v
  backend-specific execution layer
        |
        v
  compiler contract family
        |
        v
  runtime execution contract
        |
        v
  device
```

## The Three Conversations We Need To Keep Separate

```text
                 COMPILER / BACKEND SUBSTRATE

   current AIU path contract          future backend/device direction
   -------------------------          -------------------------------
   SuperDSC / SpyreCode /             PrivateUse1 device model
   JobPlan / sendnn runtime           + Inductor integration
          |                                      |
          |                                      |
          +----------------+  +------------------+
                           |  |
                           v  v
                    future IR / artifact direction
                    (KTIR is one public thread here)
```

If these are collapsed into one blob, people talk past each other:

- `vllm_spyre` engineers tend to care about the current contract family because
  that is what the current AIU path actually executes.
- `torch-spyre` engineers often mean the broader backend/device direction when
  they say the future compiler path.
- KTIR is a valid part of the future discussion, but it is only one piece of
  that broader direction.

## Current Contract Direction

Today’s public torch-spyre direction still includes the current contract family
based on:

- SuperDSC bundle
- SpyreCode / JobPlan
- the current runtime execution path

### Current Contract Picture

```text
  vllm_spyre / current plugin logic
           |
           v
     torch.compile
           |
           v
         sendnn
           |
           v
  SuperDSC bundle -> SpyreCode / JobPlan
           |
           v
      current runtime
           |
           v
          AIU
```

## Future Contract Direction

The future contract direction is more torch-spyre-native and maps, in a rough
`vllm-spyre`-facing sense, to the broader compiler/backend direction behind
`torch.compile(..., backend="inductor")` on torch-spyre.

KTIR is one public thread inside that direction, but it is not the whole
definition of it from the `vllm-spyre` point of view.

### Future Contract Picture

```text
  thinner plugin / backend logic
            |
            v
      torch.compile / Inductor
            |
            v
      torch-spyre device/runtime model
            |
            v
   future torch-spyre compiler/backend direction
            |
            v
           AIU
```

## Why This Matters For KV Features

```text
  copy semantics
  stream semantics
  tensor ownership
  runtime handles
  allocator model
      ->
  whether reuse/offload/disaggregation can be expressed cleanly
```

This is why the stack transition and the compiler/runtime transition are
related but not identical.

## Stable vs Unstable Assumptions

```text
  relatively stable
    - desire for thinner plugin surface
    - desire for upstream model-code reuse
    - need for copy and distributed maturity

  less stable
    - exact runtime artifact formats
    - exact compiler contract terminology
    - exact layering of lower substrate APIs
```

## Current Direction

Practical guidance under this topic:

- avoid hard-coding long-lived design language to fast-moving lower-contract
  details unless they are necessary
- keep high-level topic docs above the most volatile implementation details
- use compiler/runtime milestones as gating conditions for `vllm-spyre-next`
  feature migration, not as excuses to block proofs on the current path

## Communication Goal

The main communication job of this topic is to prevent higher-level design
discussions from hard-coding unstable lower-layer terminology while still being
specific enough that torch-spyre and PyTorch engineers can see what is actually
being asked of them.

## Deeper Reading

- [SuperDSC and Current Contracts](../superdsc-and-current-contracts/README.md)
- [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- [KTIR and Future IR](../ktir-and-future-ir/README.md)

## Related Source-Repos and References

- SuperDSC bundle specification:
  [torch-spyre PR #868](https://github.com/torch-spyre/torch-spyre/pull/868)
- SpyreCode / JobPlan direction:
  [torch-spyre PR #1010](https://github.com/torch-spyre/torch-spyre/pull/1010)
- KTIR direction:
  [torch-spyre issue #682](https://github.com/torch-spyre/torch-spyre/issues/682)
  - one public thread within the broader future compiler/backend direction
- Eager codegen through torch compile:
  [torch-spyre issue #183](https://github.com/torch-spyre/torch-spyre/issues/183)
- Tensor memory access analysis:
  [torch-spyre PR #1011](https://github.com/torch-spyre/torch-spyre/pull/1011)
- Spyre Device RFC:
  [RFC 0171](https://github.com/torch-spyre/torch-spyre/tree/main/RFCs/0171-SpyreDevice)
