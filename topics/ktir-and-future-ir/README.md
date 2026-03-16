# KTIR and Future IR

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This topic is the deeper map for KTIR and other future IR/artifact questions
inside the broader torch-spyre backend direction.

It is the right document when the question is:

- where does KTIR fit in the future story?
- what parts of the future direction are really IR questions?
- how much should `vllm_spyre` care about this layer right now?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Umbrella topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [SuperDSC and Current Contracts](../superdsc-and-current-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What is this topic actually about?

This topic is about the future representation and handoff layer between
Inductor/backend logic and the lower Spyre runtime world.

That includes questions like:

- what IR or artifact family is emitted?
- what layout / memory / launch information is represented there?
- what runtime consumes it?
- how much of the current `SuperDSC -> sendnn` path survives?

KTIR is one public thread in that space, but it is not the only thing that
matters.

</details>

## Keep These Layers Separate

```text
  broader backend/device direction
      |
      +--> Spyre device registration
      +--> allocator + layouts + copies
      +--> Inductor hooks and passes
      |
      v
  future IR / artifact direction
      |
      +--> KTIR is one public thread here
      |
      v
  runtime consumption / launch story
```

This is the separation Fabian was pushing toward:

- top-level `vllm_spyre` docs should stay above this level
- deeper learning docs can go here
- we should not redefine the whole future direction as “KTIR”

## Current vs Future Contract Picture

```text
   CURRENT FAMILY                                  FUTURE DIRECTION

   SuperDSC bundle                                 future IR / artifact family
        |                                                    |
   SpyreCode / JobPlan                                       |
        |                                                    |
   dxp_standalone + convert_artifacts                        |
        |                                                    |
   g2.graph.cbor + sendnn launch                             |
        |                                                    |
       AIU                                       KTIR is one public thread here
```

The key takeaway is not that KTIR replaces every box one-for-one. The real
point is that the artifact and launch boundary is evolving, and KTIR is one
public part of that evolution.

## Where the Current Code Already Shows Pressure on This Layer

Even before KTIR enters the picture directly, the current code already shows why
future IR/artifact design matters:

### 1. Layout propagation and legality

Spyre carries explicit device-layout knowledge through `FixedTiledLayout` and
custom scheduler passes because the lower layers need more than host strides.

- Code:
  [torch_spyre/_inductor/ir.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/ir.py)
- Code:
  [torch_spyre/_inductor/passes.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/passes.py)

### 2. Kernel descriptors and launch metadata

The current family emits explicit kernel descriptors with dimensions, op info,
and device-layout-aware arguments before compiling them further.

- Code:
  [torch_spyre/_inductor/runtime/async_compile.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/runtime/async_compile.py)

### 3. Lowering pressure from tiled tensors

The tiled-tensor work is not “just a runtime detail.” It affects the legal and
useful IR the compiler needs to reason about.

- RFC:
  [RFC 0047 Tiled Tensors](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0047-TiledTensors/0047-TiledTensorsRFC.md)

These are the kinds of requirements a future IR/artifact direction has to carry.

## What a Future IR / Artifact Layer Likely Has To Carry

```text
  higher-level compiled intent
          |
          v
   +-----------------------------+
   | future IR / artifact layer  |
   |                             |
   | - op/kernel identity        |
   | - layout legality           |
   | - tiled-memory metadata     |
   | - copy / residency needs    |
   | - launch / segment metadata |
   | - scratchpad assumptions    |
   +--------------+--------------+
                  |
                  v
         runtime consumption / launch
                  |
                  v
                 AIU
```

The exact object model here may change. The stable learning target is the
responsibility boundary, not any one temporary artifact name.

## A Useful Mental Model for KTIR

```text
  If the broader future direction is:

     "make torch-spyre a stronger PyTorch backend/device"

  then KTIR is more like:

     "one possible public representation / contract thread inside the
      lower compiler-to-runtime handoff"
```

That makes KTIR important for learning, but it also keeps it in the right place.

## Why `vllm_spyre` Should Care, But Not Too Early

From a serving-plugin point of view, this layer matters only indirectly today:

- it influences what future copies/layouts/launch semantics will look like
- it influences how thin `vllm-spyre-next` can eventually become
- it influences how reusable upstream `vLLM` integration can be

But it is still not the first thing to prove for current AIU KV work.

That is why the right split is:

- current proofs on the current AIU path first
- substrate maturity next
- deeper future IR/artifact understanding in parallel, so the transition does
  not surprise us later

## Public Threads to Watch

- KTIR issue:
  [torch-spyre issue #682](https://github.com/torch-spyre/torch-spyre/issues/682)
- SpyreCode / JobPlan alignment:
  [torch-spyre PR #1010](https://github.com/torch-spyre/torch-spyre/pull/1010)
- Tensor memory access analysis:
  [torch-spyre PR #1011](https://github.com/torch-spyre/torch-spyre/pull/1011)
- Spyre Device RFC:
  [RFC 0171 SpyreDevice](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0171-SpyreDevice/0171-SpyreDeviceRFC.md)
- Tiled tensor layout RFC:
  [RFC 0047 Tiled Tensors](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0047-TiledTensors/0047-TiledTensorsRFC.md)

## What To Ask in a Low-Level Conversation

- Which parts of the current artifact/launch family are expected to survive into
  the future direction?
- Is KTIR mostly a representation change, a runtime boundary change, or both?
- What new information must a future IR/artifact carry for tiled layouts,
  scratchpad planning, and copy semantics?
- Which parts of `vllm-spyre-next` should remain insulated from this churn as
  long as possible?
