# Spyre Device and Inductor

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This topic is the deeper map for the broader torch-spyre backend/device
direction that Fabian described in rough terms as the path behind
`backend="inductor"`.

It is the right document when the question is:

- what does the future torch-spyre backend direction include besides KTIR?
- what makes Spyre look like a real device/backend to PyTorch?
- which parts of that direction does `vllm-spyre-next` actually depend on?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Umbrella topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [SuperDSC and Current Contracts](../superdsc-and-current-contracts/README.md)
- Neighbor topic: [KTIR and Future IR](../ktir-and-future-ir/README.md)
- Neighbor topic: [Multi-Spyre](../multi-spyre/README.md)

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### What is this topic really about?

This topic is not just about a compiler flag. It is about the substrate that
makes Spyre behave like a first-class PyTorch backend:

- device registration
- tensor allocation and residency
- tensor layout modeling
- copy semantics
- Inductor lowering/scheduling/codegen hooks
- runtime launch hooks

That is why the future direction is broader than KTIR.

</details>

## High-Level Substrate Model

```text
           FUTURE TORCH-SPYRE BACKEND / DEVICE DIRECTION

   PyTorch eager / torch.compile / Inductor
                    |
                    v
        Spyre device registration + PrivateUse1
                    |
                    v
      Spyre tensor model + allocator + layout metadata
                    |
                    v
     Spyre-specific Inductor hooks / passes / wrapper code
                    |
                    v
        lower compiler/runtime contract / artifact family
                    |
                    v
                   AIU
```

The first four layers above are already a substantial topic even before
discussing KTIR.

## Why Fabian’s Point Matters

```text
  "future backend direction" as seen from vllm-spyre
                   !=
               "just KTIR"

  better rough picture:

    torch.compile(..., backend="inductor")
                |
                v
        torch-spyre device/backend substrate
                |
                +--> current contract family today
                +--> future IR / artifact direction over time
```

This framing keeps us from collapsing:

- the Spyre device model
- the Inductor integration layer
- the future IR/artifact direction

into a single overloaded term.

## The Concrete Substrate Pieces

### 1. Device registration and lazy runtime init

Torch-spyre registers Spyre through `PrivateUse1`, exposes a module, and lazily
starts the C++ runtime.

- Code:
  [torch_spyre/__init__.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/__init__.py)

Relevant consequences:

- Spyre becomes a PyTorch device, not just an external launcher
- the runtime is initialized through the device module
- subprocess/fork behavior is already a concern in the device layer

### 2. Device interface and device-op overrides

The current code already exposes a `DeviceInterface`, but it also shows what is
still immature:

- `current_device()` is effectively fixed to `0`
- multi-device support is still TODO
- raw streams / guards / synchronize are still stubbed

- Code:
  [torch_spyre/utils/device_interface.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/utils/device_interface.py)
- Code:
  [torch_spyre/utils/device_op_overrides.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/utils/device_op_overrides.py)

This is one of the clearest examples of why the future direction is bigger than
an IR question.

### 3. Tiled layout and tensor representation

Spyre needs more than host `size/stride`; it needs device layout metadata and a
mapping between host and device views.

```text
  host logical tensor
         |
         +--> host size/stride
         |
         +--> SpyreTensorLayout
                - device size
                - device stride
                - dim map
                - stick metadata
                - padding
```

- Code:
  [torch_spyre/_inductor/ir.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/ir.py)
- RFC:
  [RFC 0047 Tiled Tensors](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0047-TiledTensors/0047-TiledTensorsRFC.md)

### Device/layout/copy ownership seam

```text
  PyTorch tensor API
         |
         v
  Spyre device registration
         |
         v
  SpyreTensorImpl / SpyreTensorLayout
         |
         +--> allocation handle ownership
         +--> host/device dim mapping
         +--> stick + padding metadata
         |
         v
  wrapper / scheduler / codegen decisions
         |
         v
  host<->device DMA / runtime launch
```

This seam is where a lot of future serving capability will be won or lost:

- if the layout model is too weak, higher layers cannot express KV-friendly
  movement and staging cleanly
- if the copy path is too weak, local offload and P-D disaggregation will stay
  awkward even if higher-level connector logic is correct

### 4. Inductor passes and wrapper integration

Torch-spyre already plugs into Inductor with:

- custom pre/post FX passes
- scheduler passes
- layout propagation
- wrapper-time buffer allocation

```text
  Inductor graph
      |
      v
  Spyre custom passes
      |
      +--> propagate tiled layouts
      +--> plan core division
      +--> plan scratchpad usage
      |
      v
  Spyre wrapper allocates tensors with device layouts
```

- Code:
  [torch_spyre/_inductor/passes.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/passes.py)
- Code:
  [torch_spyre/_inductor/wrapper.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/wrapper.py)
- Code:
  [torch_spyre/_inductor/preload.py](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/_inductor/preload.py)

### 5. Copy path and allocator

The device/backend direction also includes the data plane:

```text
  host tensor <----> SpyreTensorLayout-aware DMA graph <----> device tensor
                                |
                                v
                     custom allocator / handles / DCI
```

- Code:
  [torch_spyre/csrc/spyre_mem.cpp](https://github.com/torch-spyre/torch-spyre/blob/main/torch_spyre/csrc/spyre_mem.cpp)

This is directly relevant to KV reuse/offload/disaggregation because those
features eventually need robust copy and residency semantics.

## Current Path vs Future Direction

```text
     current AIU execution path                     future destination shape
     -------------------------                     ------------------------
     torch.compile -> sendnn                       torch.compile -> inductor-ish
               |                                              |
               v                                              v
      current contract family                    stronger torch-spyre device model
               |                                              |
               v                                              v
              AIU                             thinner plugin + more upstream reuse
```

The left-hand side is what runs today. The right-hand side is the destination
shape we are trying to understand and prepare for.

## Why `vllm-spyre-next` Cares So Much

`vllm-spyre-next` only becomes compelling if this substrate can carry:

- upstream model code
- upstream scheduler behavior
- Spyre-specific attention/backend code
- KV-heavy serving workflows
- eventually distributed and multi-device flows

That is why this topic is central to the new stack even when KTIR is not yet
the right discussion depth for the top-level README.

## Current Public Threads

- Spyre Device RFC:
  [RFC 0171 SpyreDevice](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0171-SpyreDevice/0171-SpyreDeviceRFC.md)
- Tiled tensor layout RFC:
  [RFC 0047 Tiled Tensors](https://github.com/torch-spyre/torch-spyre/blob/main/RFCs/0047-TiledTensors/0047-TiledTensorsRFC.md)
- Eager codegen / compile-backed eager epic:
  [torch-spyre issue #183](https://github.com/torch-spyre/torch-spyre/issues/183)
- Allocator epic:
  [torch-spyre issue #200](https://github.com/torch-spyre/torch-spyre/issues/200)

## What To Ask in a Low-Level Conversation

- Which parts of the Spyre device model are already “real enough” for higher
  layers to target?
- Which missing pieces are the biggest blockers for `vllm-spyre-next`:
  streams, copies, allocator behavior, or distributed primitives?
- Which parts of the current `sendnn` path are expected to survive underneath
  the broader `backend="inductor"` direction?
- Where should serving-layer docs stay abstract because the substrate is still
  moving too fast?
