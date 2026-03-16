# Topic Index

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This directory is the structured topic map for the Spyre + vLLM planning work.

Each topic starts from first principles and then narrows toward:

- the current Spyre software stack
- `vllm-spyre-next` / the new stack
- the relevant implementation seams
- the current proof and planning direction

</details>

### Architecture and transition

- [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)
- [Execution and Attention](./execution-and-attention/README.md)
- [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)

### Compiler / backend substrate

- [SuperDSC and Current Contracts](./superdsc-and-current-contracts/README.md)
- [Spyre Device and Inductor](./spyre-device-and-inductor/README.md)
- [KTIR and Future IR](./ktir-and-future-ir/README.md)

### KV and data movement

- [KV Reuse](./kv-reuse/README.md)
- [KV Offload](./kv-offload/README.md)
- [Prefill/Decode Disaggregation](./prefill-decode-disaggregation/README.md)

### Scale and validation

- [Multi-Spyre](./multi-spyre/README.md)
- [Validation and Proof Plan](./validation-and-proof-plan/README.md)

<details markdown="1">
<summary><strong>Reading Order</strong></summary>


For someone new to the space:

1. [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)
2. [Execution and Attention](./execution-and-attention/README.md)
3. [KV Reuse](./kv-reuse/README.md)
4. [KV Offload](./kv-offload/README.md)
5. [Prefill/Decode Disaggregation](./prefill-decode-disaggregation/README.md)
6. [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)
7. [Spyre Device and Inductor](./spyre-device-and-inductor/README.md)
8. [SuperDSC and Current Contracts](./superdsc-and-current-contracts/README.md)
9. [KTIR and Future IR](./ktir-and-future-ir/README.md)
10. [Multi-Spyre](./multi-spyre/README.md)
11. [Validation and Proof Plan](./validation-and-proof-plan/README.md)

For planning the current work:

1. [KV Reuse](./kv-reuse/README.md)
2. [KV Offload](./kv-offload/README.md)
3. [Validation and Proof Plan](./validation-and-proof-plan/README.md)
4. [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)
5. [Multi-Spyre](./multi-spyre/README.md)
6. [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)

</details>

<details markdown="1">
<summary><strong>Reading By Team</strong></summary>


### Current `vllm_spyre` engineers

Start with:

1. [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)
2. [Execution and Attention](./execution-and-attention/README.md)
3. [KV Reuse](./kv-reuse/README.md)
4. [KV Offload](./kv-offload/README.md)
5. [Validation and Proof Plan](./validation-and-proof-plan/README.md)

Primary concern:

- where the real current seam is
- what can be proven now without overcommitting the long-term shape

### `vllm-spyre-next` engineers

Start with:

1. [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)
2. [Execution and Attention](./execution-and-attention/README.md)
3. [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)
4. [KV Reuse](./kv-reuse/README.md)
5. [KV Offload](./kv-offload/README.md)
6. [Spyre Device and Inductor](./spyre-device-and-inductor/README.md)

Primary concern:

- what ownership should move out of the plugin
- what must mature before advanced KV features belong on `vllm-spyre-next`

### Upstream vLLM engineers

Start with:

1. [KV Reuse](./kv-reuse/README.md)
2. [KV Offload](./kv-offload/README.md)
3. [Prefill/Decode Disaggregation](./prefill-decode-disaggregation/README.md)
4. [Current Path and vllm-spyre-next](./current-vs-next-stack/README.md)

Primary concern:

- which semantics should align with upstream connector/offload/disaggregation
  language
- where Spyre is temporarily carrying custom seams

### `torch-spyre` engineers

Start with:

1. [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)
2. [Spyre Device and Inductor](./spyre-device-and-inductor/README.md)
3. [SuperDSC and Current Contracts](./superdsc-and-current-contracts/README.md)
4. [KTIR and Future IR](./ktir-and-future-ir/README.md)
5. [Execution and Attention](./execution-and-attention/README.md)
6. [Multi-Spyre](./multi-spyre/README.md)
7. [KV Offload](./kv-offload/README.md)
8. [Prefill/Decode Disaggregation](./prefill-decode-disaggregation/README.md)

Primary concern:

- which lower-level capabilities the higher-level plan depends on
- which substrate assumptions should stay abstract versus become explicit

### PyTorch / distributed / runtime engineers

Start with:

1. [Compiler/Runtime Contracts](./compiler-runtime-contracts/README.md)
2. [Spyre Device and Inductor](./spyre-device-and-inductor/README.md)
3. [KTIR and Future IR](./ktir-and-future-ir/README.md)
4. [Multi-Spyre](./multi-spyre/README.md)
5. [Prefill/Decode Disaggregation](./prefill-decode-disaggregation/README.md)

Primary concern:

- distributed/copy/stream/collective implications
- which assumptions are PyTorch-level versus Spyre-specific

</details>

## What Good Cross-Team Communication Looks Like

These docs work best when they help people separate:

- stable architecture goals from fast-moving implementation details
- proof seams on the current `vllm_spyre` path from destination seams on
  `vllm-spyre-next`
- logical connector semantics from backend-specific translation details
- evidence we already have from evidence we still need
