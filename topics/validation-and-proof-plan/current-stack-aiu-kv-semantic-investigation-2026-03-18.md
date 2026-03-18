# Current-Stack AIU KV Semantic Investigation

Last updated: 2026-03-18

This page records the follow-on AIU investigation that tested semantic
correctness of external KV save/load on the current `vllm_spyre` stack after the
initial reuse and prefix-caching results.

It is a companion to:

- [Current-Stack AIU KV Status (2026-03-17)](./current-stack-aiu-kv-status-2026-03-17.md)
- [Current-Stack AIU KV Data](./current-stack-aiu-kv-data.md)

## Scope

- Stack: current `vllm_spyre`
- Hardware scope: single AIU card
- Goal:
  - test whether external KV offload/reload on the current stack preserves
    semantic correctness, not just block accounting and latency behavior

## Summary

- The semantic loadback test failed on the current stack.
- This failure reproduced on both:
  - `host_memory`
  - `serialized_shared_memory_service`
- A follow-on probe found and fixed a stale-reference bug in the experimental
  connector path.
- After fixing stale references, semantic mismatch still remained.

## Published Runs

### `r17`: semantic cold-vs-reuse comparison

Runs:

- `r17a-semantic-host-java-p384-o8`
- `r17b-semantic-host-powerquery-p384-o8`
- `r17c-semantic-shm-java-p384-o8`
- `r17d-semantic-shm-powerquery-p384-o8`

Common shape:

- actual prompt templates
- deterministic generation
- `384` prompt tokens
- `8` output tokens
- exact and partial reuse both exercised

Observed result:

- all four runs loaded KV blocks on reuse
- all four runs diverged semantically between cold and reuse continuation

Representative case:

- `r17a` exact cold:
  - `'\nThe reader wants a quick, practical'`
- `r17a` exact reuse:
  - `' 1000000'`
- `r17a` exact reuse blocks loaded:
  - `48`

Interpretation:

- the current path was proving a real control path
- but not proving semantically correct external KV offload/reload

### `r18a`: semantic probe on simplest host-memory path

Run:

- `r18a-semantic-probe-host-java-p384-o8`

Code under test:

- env-gated semantic probe added on public branch
- [`spyre_kv_semantic_probe.py`](https://github.com/toddllm/vllm-spyre/blob/42c6d4f9e7334e9c88f3271f4a8f0d7fbf22ea51/vllm_spyre/v1/worker/spyre_kv_semantic_probe.py)

Observed result:

- semantic mismatch still reproduced
- probe logs showed the connector-visible registered KV tensors had gone stale
- the current model tensors had different object identities and different data
  pointers later in the run

Interpretation:

- the initial experimental path had a real stale-reference bug

### `r18b`: stale-reference repair on same host-memory probe

Run:

- `r18b-semantic-probe-host-java-p384-o8`

Code under test:

- load/save sync changed to target the current model tensors when available
- [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/v1/worker/spyre_model_runner.py)
- regression test:
  - [`test_spyre_model_runner_kv_sync.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/tests/v1/worker/test_spyre_model_runner_kv_sync.py)

Observed result:

- the stale-reference problem improved materially
- probe logs showed registered and current model tensors aligned at load time
- staging updated from the current model tensors on save
- semantic mismatch still remained

Representative case:

- exact cold:
  - `'\nThe reader wants a quick, practical'`
- exact reuse:
  - `' 1000000'`
- exact reuse blocks loaded:
  - `48`

Interpretation:

- stale references were one real bug
- but they were not the root semantic issue

## Conclusion

The current-stack semantic investigation established the following:

- current-stack block accounting and reuse-related latency improvements were real
- the initial experimental path also had a stale-reference bug
- after repairing that bug, semantically correct external KV offload/reload was
  still not established on the current stack

The durable result is that the current-stack tensor surface used in the
experiment was not sufficient to prove semantically correct external KV
offload/reload.

## What This Page Does And Does Not Claim

Confirmed here:

- semantic cold-vs-reuse testing was performed on AIU
- the current-stack semantic offload/reload path did not pass that test
- one stale-reference bug was found and repaired during the investigation

Not claimed here:

- that current-stack external KV offload/reload is a supported feature
- that the current stack is the right long-term implementation target for KV
  offload
- that `vllm-spyre-next` is already ready for the same feature work
