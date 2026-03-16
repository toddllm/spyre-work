# SuperDSC and Current Contracts

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This topic is the low-level map for the current torch-spyre contract family that
the current AIU path still depends on.

It is the right document when the question is:

- what exactly sits under `torch.compile -> sendnn` today?
- where do `SuperDSC`, `SpyreCode`, `JobPlan`, `g2`, and the runtime fit?
- what does `vllm_spyre` actually feel from that layer?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Umbrella topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- Neighbor topic: [KTIR and Future IR](../ktir-and-future-ir/README.md)

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What is a contract family here?

For this work, a compiler/runtime contract family is the concrete set of things
the compiler emits and the runtime expects:

- artifact formats
- tensor argument conventions
- layout assumptions
- launch semantics
- copy semantics

The important point is that the current AIU path is not just “Inductor on
Spyre.” It is a specific current family of artifacts and launch steps.

</details>

## Current AIU Path in One Picture

```text
             CURRENT AIU PATH (WHAT RUNS TODAY)

  PyTorch graph / compiled region
               |
               v
      torch.compile(..., backend="sendnn")
               |
               v
     torch-spyre scheduling + SDSC codegen
       |               |                |
       |               |                +--> layout + arg metadata
       |               |
       |               +--> sdsc.json
       |
       +--> kernel wrapper / async compile glue
               |
               v
         dxp_standalone compile
               |
               v
      convert_artifacts(...) -> g2.graph.cbor
               |
               v
        launchKernel(g2, tensor args)
               |
               v
       sendnn::GraphLoader / flex runtime
               |
               v
                AIU
```

The labels above are why Fabian’s distinction matters:

- the current AIU path is concretely `torch.compile -> sendnn`
- it is backed by the current artifact/launch family
- it should not be conflated with the future torch-spyre backend direction

## The Current Family End to End

```text
      TORCH / INDUCTOR SIDE                         RUNTIME SIDE

  +---------------------------+          +----------------------------+
  | SpyrePythonWrapperCodegen |          | C++ launch/runtime bridge  |
  | wrapper.py                |          | module.cpp                 |
  +-------------+-------------+          +-------------+--------------+
                |                                      ^
                v                                      |
  +---------------------------+                        |
  | SuperDSCScheduling        |                        |
  | dsc.py                    |                        |
  +-------------+-------------+                        |
                |                                      |
                v                                      |
  +---------------------------+                        |
  | generate_sdsc(...)        |                        |
  | codegen/superdsc.py       |                        |
  +-------------+-------------+                        |
                |                                      |
                v                                      |
         kernel descriptor                             |
         + layout / arg map                            |
                |                                      |
                v                                      |
  +---------------------------+                        |
  | SpyreAsyncCompile.sdsc    |                        |
  | runtime/async_compile.py  |                        |
  +-------------+-------------+                        |
                |                                      |
                +--> write sdsc.json                   |
                +--> run dxp_standalone                |
                +--> convert_artifacts(...) -----------+
                            |
                            v
                     g2.graph.cbor
                            |
                            v
                  SpyreSDSCKernelRunner.run
                  runtime/kernel_runner.py
                            |
                            v
                    launch_kernel(...)
                            |
                            v
                sendnn GraphLoader + flex Runtime
                            |
                            v
                           AIU
```

## What `vllm_spyre` Feels From This Layer

From the plugin’s point of view, this layer matters through consequences, not
through artifact names:

- whether tensor layouts can be represented cleanly
- whether host/device copies exist for the layouts we need
- whether the runtime can tolerate the batching and warmup patterns the plugin
  uses
- whether execution is stable enough for KV-heavy serving behavior

That is why top-level `vllm_spyre` docs should not over-focus on KTIR. The
current serving path mostly feels the current contract family via runtime
behavior, copies, and layout legality.

## The Concrete Code Seams

### 1. Wrapper and kernel-definition seam

The Spyre wrapper injects Spyre-specific runtime types and allocates tensors
with `SpyreTensorLayout` when a `FixedTiledLayout` is present.

- Code:
  [torch_spyre/_inductor/wrapper.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/wrapper.py)

### 2. Scheduling and SDSC code generation seam

The current family is still explicitly named in the scheduling path:

- `SuperDSCScheduling`
- `generate_sdsc(...)`

- Code:
  [torch_spyre/_inductor/dsc.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/dsc.py)
- Code:
  [torch_spyre/_inductor/codegen/superdsc.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/codegen/superdsc.py)

### 3. Async compile and artifact conversion seam

This is where the emitted descriptor becomes `sdsc.json`, is compiled with
`dxp_standalone`, and is converted into the launchable graph artifact.

- Code:
  [torch_spyre/_inductor/runtime/async_compile.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/runtime/async_compile.py)

### 4. Runtime launch seam

The kernel runner eventually calls `launch_kernel`, which loads the compiled
graph, patches in tensor bindings, compiles/parses it with `sendnn::GraphLoader`,
and executes through the runtime.

- Code:
  [torch_spyre/_inductor/runtime/kernel_runner.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/runtime/kernel_runner.py)
- Code:
  [torch_spyre/csrc/module.cpp](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/csrc/module.cpp)

### 5. Copy and DMA seam

The current family also includes a concrete copy story built around generated
DMA graphs and `SenDataConvert`-style host/device preparation.

- Code:
  [torch_spyre/csrc/spyre_mem.cpp](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/csrc/spyre_mem.cpp)

### Current copy path in more detail

```text
     host tensor + host stride view
                 |
                 v
      SpyreTensorLayout + dim_map + padding
                 |
                 v
         generate_dci(...)
                 |
                 v
  SenHostCompute("SenDataConvert", dci)
                 |
                 v
         SenDataTransfer DMA graph
                 |
                 v
      device tensor / handle / allocation
                 |
                 v
                AIU
```

That is the concrete kind of machinery the current serving path is leaning on
when it stages tensors, moves them, or reasons about residency.

## Why This Matters for KV Reuse / Offload / P-D Disaggregation

```text
  KV feature idea
      |
      v
  needs staging tensor / copy / residency story
      |
      v
  copy path + layout legality + launch stability
      |
      v
  current contract family determines whether it is practical today
```

For current-path `vllm_spyre`, the immediate questions are not “is KTIR ready?”
They are:

- can the current path move and stage the right tensors safely?
- can it preserve layout expectations?
- can it execute the resulting copies and kernels reliably enough on AIU?

## Current Public Artifacts and Design Threads

- SuperDSC bundle specification:
  [torch-spyre PR #868](https://github.com/torch-spyre/torch-spyre/pull/868)
- SpyreCode / JobPlan alignment:
  [torch-spyre PR #1010](https://github.com/torch-spyre/torch-spyre/pull/1010)
- Tensor memory access analysis:
  [torch-spyre PR #1011](https://github.com/torch-spyre/torch-spyre/pull/1011)

## What To Ask in a Low-Level Conversation

- Which parts of the current family are actually stable enough for higher
  layers to rely on?
- Is `SpyreCode / JobPlan` still best thought of as current-family evolution, or
  already part of the future direction?
- Which current copy or artifact assumptions are most likely to break as the
  future direction hardens?
- For current AIU proofs, what runtime/copy constraints should the `vllm_spyre`
  team explicitly budget for?
