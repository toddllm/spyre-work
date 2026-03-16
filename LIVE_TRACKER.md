# Spyre Live Tracker

Status: Tracking note

Last updated: 2026-03-16

## Purpose

This file is the compact watch list for public work that is likely to change
the shape of the Spyre + vLLM roadmap.

It is intentionally more tactical than the
[big-picture README](./README.md).

## vllm-spyre

### Next-stack direction

- [#639 `[RFC] vllm-spyre-next`](https://github.com/vllm-project/vllm-spyre/issues/639)
  - Current architecture rationale and target end-state for reducing plugin
    footprint.
  - Strongest public statement of old-stack vs next-stack motivation.

- [#761 `[Epic] vllm-spyre-next dev/test readiness`](https://github.com/vllm-project/vllm-spyre/issues/761)
  - Indicates that `Spyre-Next` is still in basic readiness and packaging/test
    maturation, not yet complete serving-path maturity.

- [#664 `Build image with old stack and new stack side-by-side`](https://github.com/vllm-project/vllm-spyre/issues/664)
  - Important operationally because the transition period likely requires both
    stacks to coexist for some time.

### Attention / model execution

- [#666 `run vLLM instead of fms modeling code (CPU-only)`](https://github.com/vllm-project/vllm-spyre/issues/666)
  - Key next-stack milestone: remove FMS dependency on the execution side.

- [#647 `Contiguous KV-cache implementation of AttentionBackend using torch-spyre`](https://github.com/vllm-project/vllm-spyre/issues/647)
  - "Proof of life" backend before fully paged attention.

- [#648 `Paged KV-cache implementation of AttentionBackend using torch-spyre`](https://github.com/vllm-project/vllm-spyre/issues/648)
  - Critical next-stack prerequisite for serious KV/offload work.

- [#689 `Layer-wise split-execution of vLLM in torch-spyre`](https://github.com/vllm-project/vllm-spyre/issues/689)
  - Useful transition concept: mixed CPU/Spyre execution instead of full
    cutover.

### Current-stack KV connector / offload direction

- [#745 `[Epic] Develop KVCacheConnector for Spyre`](https://github.com/vllm-project/vllm-spyre/issues/745)
  - Most directly aligned issue for old-stack offload / llm-d / PD-disagg.

### Active PRs

- [#798 `Integrated custom attention backend`](https://github.com/vllm-project/vllm-spyre/pull/798)
  - Attention backend skeleton in `Spyre-Next`.

- [#826 `Update vllm and torch-spyre`](https://github.com/vllm-project/vllm-spyre/pull/826)
  - Important because version drift here can change what is feasible in the
    next stack.

- [#836 `Wrapped Embedding layer for spare`](https://github.com/vllm-project/vllm-spyre/pull/836)
  - Example of wrapped upstream layer strategy in the next stack.

- [#837 `RMSNorm tests and upstream tests framework`](https://github.com/vllm-project/vllm-spyre/pull/837)
  - Relevant because it improves next-stack compatibility signal.

## upstream vLLM

### KV offload / HMA

- [#37160 `[Feat][v1] Simple yet General CPU KV Cache Offloading`](https://github.com/vllm-project/vllm/pull/37160)
  - Important for the offload design direction because it moves toward simpler,
    more general infrastructure and explicitly reuses existing block/cache
    machinery.

- [#36642](https://github.com/vllm-project/vllm/pull/36642),
  [#36644](https://github.com/vllm-project/vllm/pull/36644),
  [#36645](https://github.com/vllm-project/vllm/pull/36645)
  - Multi-group HMA, event simplification, sliding-window lookup.
  - These look like plumbing pieces that broaden what the connector layer can
    represent.

- [#35223](https://github.com/vllm-project/vllm/pull/35223)
  - Scheduler-side HMA load recovery.

- [#36549](https://github.com/vllm-project/vllm/pull/36549)
  - `MultiConnector` + `SupportsHMA` fix; important for sub-connector
    composition.

### P-D disaggregation / NIXL

- [#35264 `Support KV push from Prefill to Decode node using Nixl KV Connector`](https://github.com/vllm-project/vllm/pull/35264)
  - Strongest public PR for the P->D KV push pattern.

- [#35760 `Add PD disagg + SD acceptance tests`](https://github.com/vllm-project/vllm/pull/35760)
  - Useful because it turns PD-disagg into explicit end-to-end validation.

- [#36687 `Add support for hybrid SSM-FA models`](https://github.com/vllm-project/vllm/pull/36687)
  - Important because real disaggregated deployments need more than "plain"
    FA-only models.

- [#36957 `Exploring heterogeneous TP in hybrid SSM-FA P/D disaggregation`](https://github.com/vllm-project/vllm/pull/36957)
  - Especially relevant to any future multi-Spyre + PD story.

- [#36780 RFC issue for hybrid SSM-FA NIXL connector support](https://github.com/vllm-project/vllm/issues/36780)
  - Worth watching for design language and constraints.

## torch-spyre

### Distributed / multi-Spyre

- [#816 `Multi-Spyre Device Support Framework`](https://github.com/torch-spyre/torch-spyre/pull/816)
  - Adds `spyreccl` and a distributed backend story.
  - Highest-value public thread for next-stack multi-Spyre.

- [issue #99 `Multi-Device Support Investigation`](https://github.com/torch-spyre/torch-spyre/issues/99)
  - Broader tracking issue behind the same theme.

### Runtime and transport prerequisites

- [#918 `Add Stream Support for Torch-Spyre`](https://github.com/torch-spyre/torch-spyre/pull/918)
  - Important for async and overlap concepts.

- [#1007 `graph-free copy`](https://github.com/torch-spyre/torch-spyre/pull/1007)
  - Important for host↔device movement without per-copy graph compilation.

- [issue #200 `Investigation into new allocator which support VF Mode`](https://github.com/torch-spyre/torch-spyre/issues/200)
  - Important because allocator/handle constraints affect realistic device
    tensor management.

### Compiler/runtime contract

- [#868 `Superdsc bundle Specification`](https://github.com/torch-spyre/torch-spyre/pull/868)
  - Current compiler-interface shape.

- [issue #277](https://github.com/torch-spyre/torch-spyre/issues/277) /
  [#1010 `SpyreCode / JobPlan`](https://github.com/torch-spyre/torch-spyre/pull/1010)
  - Runtime execution contract, including H2D/D2H and program-correction steps.

- [issue #682 `Kernel Tile Intermediate Representation`](https://github.com/torch-spyre/torch-spyre/issues/682)
  - Future compiler contract replacing the current SuperDSC path.

- [#1011 `Tensor Memory Access Analysis`](https://github.com/torch-spyre/torch-spyre/pull/1011)
  - Relevant to device layout, work division, and eventually performance of
    attention/copy-heavy paths.

### Tooling / debugging

- [issue #601](https://github.com/torch-spyre/torch-spyre/issues/601) /
  [#1049 `Spyre Profiling Toolkit`](https://github.com/torch-spyre/torch-spyre/pull/1049)
  - Important for eventual AIU-side visibility once the next stack starts
    carrying meaningful workloads.

### PyTorch integration foundation

- [RFC 0171: Spyre Device](https://github.com/torch-spyre/torch-spyre/tree/main/RFCs/0171-SpyreDevice)
  - PrivateUse1 device integration and long-term torch-spyre direction.

- [issue #183 `Eager Codegen through torch compile`](https://github.com/torch-spyre/torch-spyre/issues/183)
  - Important because it replaces graph-builder-centric eager execution with a
    more PyTorch-native path.

## PyTorch upstream

- PyTorch dev-discuss:
  [IBM Spyre Accelerator: PyTorch Enabling Status and Feature Plan - 1H 2026](https://dev-discuss.pytorch.org/t/ibm-spyre-accelerator-pytorch-enabling-status-and-feature-plan-1h-2026/3319)
  - strongest public roadmap statement for the next-stack / torch-spyre
    direction
  - especially relevant to multi-Spyre because it lays out the staged plan:
    compiled functional collectives first, then `torch.distributed`, then
    eventual `torch.comms`
  - also relevant to this KV-offload discussion because it explicitly centers
    single-card production inference first and treats multi-card enablement as
    a later but planned track

- [pytorch/pytorch#172154](https://github.com/pytorch/pytorch/pull/172154)
  - PrivateUse1 backend integration with Kineto.
  - Directly relevant to torch-spyre profiling integration.

- [pytorch/pytorch#176877](https://github.com/pytorch/pytorch/issues/176877)
  - Distributed support for OpenReg.
  - Best public reference for out-of-tree accelerator distributed backend
    integration.

- [pytorch/pytorch#175954](https://github.com/pytorch/pytorch/issues/175954)
  - RFC about decomposition-table handling in Inductor.
  - Relevant because out-of-tree accelerator backends need stable compilation
    hooks.

## What To Re-check Regularly

- `vllm-spyre` PRs [#826](https://github.com/vllm-project/vllm-spyre/pull/826), [#836](https://github.com/vllm-project/vllm-spyre/pull/836), [#837](https://github.com/vllm-project/vllm-spyre/pull/837)
- upstream `vllm` PRs [#37160](https://github.com/vllm-project/vllm/pull/37160), [#35264](https://github.com/vllm-project/vllm/pull/35264), [#36687](https://github.com/vllm-project/vllm/pull/36687), [#36957](https://github.com/vllm-project/vllm/pull/36957)
- `torch-spyre` PRs [#816](https://github.com/torch-spyre/torch-spyre/pull/816), [#918](https://github.com/torch-spyre/torch-spyre/pull/918), [#1007](https://github.com/torch-spyre/torch-spyre/pull/1007), [#1049](https://github.com/torch-spyre/torch-spyre/pull/1049)
- any movement on [issue #682 (`KTIR`)](https://github.com/torch-spyre/torch-spyre/issues/682)
- the [PyTorch dev-discuss roadmap thread for Spyre in 1H 2026](https://dev-discuss.pytorch.org/t/ibm-spyre-accelerator-pytorch-enabling-status-and-feature-plan-1h-2026/3319)

## Questions To Keep In Mind

- When does next-stack attention maturity become good enough to justify AIU
  offload experiments there?
- Which upstream vLLM connector changes should we mirror in our local naming
  and architecture descriptions now, to avoid churn later?
- Which torch-spyre runtime/compiler milestones are strictly required before
  next-stack PD-disagg or offload work becomes realistic?
