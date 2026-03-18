# Validation and Proof Plan

Last updated: 2026-03-17

This topic defines the validation order and evidence thresholds used in this
repository.

Related pages:

- [Top-level index](../../README.md)
- [Current Path and vllm-spyre-next](../current-vs-next-stack/README.md)
- [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- [KV Reuse](../kv-reuse/README.md)
- [Multi-Spyre](../multi-spyre/README.md)

## Evidence Ladder

```text
  conceptual coherence
      ->
  code-level correctness
      ->
  local CPU / dev validation
      ->
  single-card AIU validation
      ->
  serving-path validation
      ->
  multi-card / distributed validation
```

## Generic Validation Sequence

```text
  first-principles design
      ->
  narrow functional proof
      ->
  observability proof
      ->
  single-card hardware proof
      ->
  serving-path proof
      ->
  scale-out proof
```

## Stack-Specific Validation

```text
  current vllm-spyre path
    -> better place for early hardware proof
    -> less architectural purity

  `vllm-spyre-next`
    -> better long-term destination
    -> depends on more unfinished substrate work
```

So the validation plan should not force both stacks to carry the same burden at
the same time.

## Current Practical Proof Strategy

### Current vllm-spyre path first

Use the current `vllm_spyre` path to prove:

- single-card AIU functional correctness
- local reuse value
- current-stack control-path and observability behavior
- observability and benchmark shape

### vllm-spyre-next later

Use `vllm-spyre-next` to prove:

- execution maturity
- backend maturity
- future architectural viability
- eventual migration destination

### Multi-Spyre later still

Use the multi-device track to prove:

- scale-out viability
- disaggregation viability
- topology-aware deployment viability

## Validation Matrix

```text
  Topic                              First proof target
  --------------------------------   -------------------------------
  KV reuse                           current vllm-spyre path, single-card AIU
  KV offload                         exploratory current-stack checks, then next-stack target
  P/D disaggregation                 later, after reuse/offload semantics
  vllm-spyre-next architecture       local + targeted AIU maturity checks
  multi-Spyre                        later distributed / topology work
```

## What Must Be Recorded For Any Serious Proof

```text
  exact stack / branch / version
  environment details
  what was measured
  what was not measured
  what assumptions were hidden
  what remains unproven
```

## Current Report Snapshot

- [Current-Stack AIU KV Status (2026-03-17)](./current-stack-aiu-kv-status-2026-03-17.md)
  - current-stack reuse proof status
  - precise current-stack non-claims
  - server-path prefix-caching result on AIU
  - report-ready current-stack status snapshot
- [Current-Stack AIU KV Semantic Investigation (2026-03-18)](./current-stack-aiu-kv-semantic-investigation-2026-03-18.md)
  - `r17` and `r18` cold-vs-reuse correctness results
  - stale-reference repair and remaining semantic mismatch
  - clarified boundary for current-stack external KV offload claims
- [Current-Stack AIU KV Data](./current-stack-aiu-kv-data.md)
  - ranked reuse benchmark results
  - full run registry with commands and parameters
  - published AIU prefix-cache probe result

## Related Working Documents

- Big-picture planning note:
  [../../README.md](../../README.md)
- Working research draft:
  [spyre-kv-offload-research.md](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/docs/roadmaps/spyre-kv-offload-research.md)
- Working RFC draft:
  [spyre-kv-offload-rfc-draft.md](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/docs/roadmaps/spyre-kv-offload-rfc-draft.md)
- P/D acceptance tests upstream:
  [vLLM PR #35760](https://github.com/vllm-project/vllm/pull/35760)
