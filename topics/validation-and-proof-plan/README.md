# Validation and Proof Plan

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the umbrella topic for how to prove architecture and feature
directions in the Spyre + vLLM story.

It is the best starting point when the question is:

- what counts as a real proof?
- what should be tested locally first?
- what should be proven on AIU first?
- how should validation differ between the current `vllm_spyre` path and
  `vllm-spyre-next`?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [Current Path and vllm-spyre-next](../current-vs-next-stack/README.md)
- Neighbor topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- Neighbor topic: [KV Reuse](../kv-reuse/README.md)
- Neighbor topic: [Multi-Spyre](../multi-spyre/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- what counts as a serious AIU proof on the current `vllm_spyre` path
- what to measure and what not to overclaim

### `vllm-spyre-next` engineers

This topic should answer:

- what kinds of readiness checks matter now
- what should not yet be treated as a hard product-level proof burden

### Upstream vLLM engineers

This topic should answer:

- what evidence from Spyre work is architecture-relevant versus purely local
- where semantic alignment matters more than raw benchmark numbers

### `torch-spyre` / PyTorch engineers

This topic should answer:

- what substrate milestones need proof at their own layer
- how lower-layer maturity should feed into `vllm-spyre-next` proof claims

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### Why is a proof plan its own topic?

Because architecture conversations often fail when people mix together very
different kinds of evidence.

For example:

- "the code compiles"
- "a local unit test passes"
- "offline latency improved"
- "serving TTFT improved on AIU"
- "multi-device disaggregation works"

Those are all useful, but they are not equivalent.

</details>

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

## Why the Current Path and New Stack Need Different Proof Plans

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
- first offload semantics
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
  KV offload                         current vllm-spyre path, single-card AIU
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

## Current Direction

The practical validation posture right now should be:

- prove near-term value where the real AIU seam already exists
- do not over-claim what local or offline results mean
- keep `vllm-spyre-next` moving without forcing it to carry every proof burden
- keep the meta docs honest about what is proven, plausible, and still open

## Current Report Snapshot

- [Current-Stack AIU KV Status (2026-03-17)](./current-stack-aiu-kv-status-2026-03-17.md)
  - current-stack reuse proof status
  - precise offload story and non-claims
  - next critical-path validation before broader report-out

## Communication Goal

The main communication job of this topic is to give all teams a shared evidence
ladder so people stop talking past each other about whether something is
"proven," "promising," or still only "plausible."

## Related Working Documents

- Big-picture planning note:
  [../../README.md](../../README.md)
- Working research draft:
  [spyre-kv-offload-research.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-research.md)
- Working RFC draft:
  [spyre-kv-offload-rfc-draft.md](https://github.com/toddllm/vllm-spyre/blob/codex/spyre-kv-slice-inmemory/docs/roadmaps/spyre-kv-offload-rfc-draft.md)
- P/D acceptance tests upstream:
  [vLLM PR #35760](https://github.com/vllm-project/vllm/pull/35760)
