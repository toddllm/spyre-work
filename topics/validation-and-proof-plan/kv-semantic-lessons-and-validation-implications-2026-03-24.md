# KV Semantic Lessons And Validation Implications

Last updated: 2026-03-24

This note records the durable public lessons from the current-stack semantic
investigation and explains how those lessons should influence ongoing work in:

- current `vllm_spyre`
- `vllm-spyre-next`
- `torch-spyre`
- prefill/decode and `llm-d` style disaggregation work

It is intentionally about **proof interpretation and validation discipline**.
It is **not** a new public feature report.

Companion pages:

- [Current-Stack AIU KV Status (2026-03-17)](./current-stack-aiu-kv-status-2026-03-17.md)
- [Current-Stack AIU KV Semantic Investigation (2026-03-18)](./current-stack-aiu-kv-semantic-investigation-2026-03-18.md)
- [Current-Stack AIU KV Data](./current-stack-aiu-kv-data.md)

## The Narrow Public Result

The public semantic failure result from `r17` and `r18` should be read
narrowly:

- the tested worker-side `past_key_value_states -> staging -> connector` surface
  did **not** preserve semantics
- fixing one stale-reference bug was necessary
- but semantic mismatch remained after that fix

That remains a valid public result.

What it does **not** establish:

- that every possible current-stack KV surface must fail
- that `vllm-spyre-next` inherits the same failure automatically
- that `torch-spyre` cannot support a semantically correct KV/runtime contract

The result is about the **tested surface**, not a blanket verdict on every
possible substrate.

## Durable Public Lessons

### 1. Latency and block accounting are not semantic proof

The current-stack AIU work already showed that:

- blocks can load
- latency can improve
- and generation can still be wrong

So public-facing proof must not stop at:

- `blocks_loaded > 0`
- lower latency
- store-path activity

It must include semantic equality checks too.

### 2. Semantic checks should prefer token ids

Output text is useful for readability, but the stronger acceptance bar is:

- compare generated token ids
- not just human-readable strings

This avoids ambiguity from formatting, whitespace, and decoding quirks.

### 3. Exact and partial reuse must both be tested

A KV path is not serious if it only survives:

- exact replay

It also needs to survive:

- partial replay with a shared prefix and divergent suffix

The public validation bar should keep both cases.

### 4. Sequential handoff is stronger than paired benchmark alone

A paired benchmark is useful, but a stronger proof slice is:

- cold baseline
- prefill/store
- later decode/load
- explicit semantic comparison versus the baseline

That structure matters for both current-stack experiments and future
disaggregation work.

### 5. The authoritative KV surface must be identified explicitly

The public semantic investigation showed that a convenient or exposed tensor
surface may not be the same thing as the **authoritative execution/runtime
surface**.

So any future public proof should state clearly:

- what surface is being tested
- why that surface is believed to be authoritative
- what remains unproven about that assumption

### 6. Same-process/runtime assumptions matter

The current stack taught a general lesson that transfers beyond one branch:

- semantic KV work is not only about serialization or transport
- it is also about the runtime contract around device ownership, layout, and
  authoritative state

That lesson applies directly to `torch-spyre` and next-stack work even when the
implementation details differ.

## Why This Matters For The Next Stack

The lessons above carry forward closely into `vllm-spyre-next` and
`torch-spyre`.

### `vllm-spyre-next`

The next-stack target should inherit the stronger public proof bar:

- token-level semantic checks
- exact and partial cases
- sequential handoff tests, not only paired reuse benchmarks
- explicit statement of the trusted KV/runtime surface

### `torch-spyre`

For `torch-spyre`, the important public implication is:

- higher layers need a clear substrate contract for what counts as the
  authoritative execution/runtime KV surface

Without that clarity, upper layers risk proving behavior on a convenient but
non-authoritative representation.

### `llm-d` / prefill-decode disaggregation

Disaggregation work depends on the same core discipline:

- the saved state has to be semantically authoritative
- the resume/load path has to be validated by token-level correctness
- paired benchmark wins alone are not enough

## Public Next Steps

The public-facing next steps should be:

1. keep the published current-stack semantic result scoped to the tested
   staging/tensor surface
2. improve public validation harnesses so semantic regressions fail loudly
3. require exact + partial semantic checks for serious KV claims
4. require sequential handoff proofs for stronger offload/disaggregation claims
5. keep `vllm-spyre-next` and `torch-spyre` work aligned around the same
   semantic acceptance bar

## What This Page Does And Does Not Claim

Claimed here:

- the published semantic failure result is scoped
- the stronger proof bar should now be part of public work
- the lessons transfer directly to next-stack and substrate work

Not claimed here:

- a new public current-stack offload implementation result
- that the current stack is the long-term public implementation target
- that `vllm-spyre-next` or `torch-spyre` already satisfy the stronger proof bar
