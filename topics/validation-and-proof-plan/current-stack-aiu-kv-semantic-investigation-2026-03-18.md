# Current-Stack AIU KV Semantic Investigation

Last updated: 2026-03-24

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

## Code Path Under Test

The current-stack experiment used the `past_key_value_states` surface exposed by
the model runner and then staged that surface through the connector path.

The exact public code calls were:

1. Registration after warmup in [`spyre_worker.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/v1/worker/spyre_worker.py#L283-L332)
   - `kv_caches = getattr(self.model_runner.model, "past_key_value_states", None)`
   - `kv_caches_dict[layer_name] = torch.stack([k_cache, v_cache])`
   - `connector.register_kv_caches(kv_caches_dict)`
2. FMS forward in [`spyre.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/model_executor/model_loader/spyre.py#L444-L459)
   - `output = self.fms_model(... past_key_value_states=self.past_key_value_states, use_cache=True, ...)`
   - `logits, self.past_key_value_states = output`
3. Loadback into the model surface in [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/v1/worker/spyre_model_runner.py#L775-L874)
   - `target_k_cache, target_v_cache = self._resolve_connector_copy_pair(...)`
   - `target_k_cache.copy_(kv_tensor[0])`
   - `target_v_cache.copy_(kv_tensor[1])`
4. Save back out to staging in [`spyre_model_runner.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/v1/worker/spyre_model_runner.py#L875-L958)
   - `source_k_cache, source_v_cache = self._resolve_connector_copy_pair(...)`
   - `kv_tensor[0].copy_(source_k_cache)`
   - `kv_tensor[1].copy_(source_v_cache)`
5. Probe sampling in [`spyre_kv_semantic_probe.py`](https://github.com/toddllm/vllm-spyre/blob/85afe2c80989c80f30c23b29dbfcd29290c33914/vllm_spyre/v1/worker/spyre_kv_semantic_probe.py#L42-L138)
   - sampled one layer / block / head slice
   - logged object identity, `data_ptr()`, sample values, and checksum

This is important because the investigation was not only comparing latency. It
was specifically testing the public `past_key_value_states` -> staging ->
loadback/sync path shown above.

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

Representative values:

| Run | Backend | Template | Exact cold | Exact reuse | Exact blocks loaded | Partial cold | Partial reuse | Partial blocks loaded |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: |
| `r17a` | `host_memory` | `java_char_to_string` | `'\nThe reader wants a quick, practical'` | `' 1000000'` | `48` | `'\nThe reader wants a quick, practical'` | `' 1999999'` | `40` |
| `r17b` | `host_memory` | `power_query_columns` | `'\nThe user is a beginner and'` | `' 1000000'` | `48` | `'\nThe user is a beginner and'` | `' 1000000'` | `40` |
| `r17c` | `serialized_shared_memory_service` | `java_char_to_string` | `'\nThe reader wants a quick, practical'` | `' 1000000'` | `48` | `'\nThe reader wants a quick, practical'` | `' 1999999'` | `40` |
| `r17d` | `serialized_shared_memory_service` | `power_query_columns` | `'\nThe user is a beginner and'` | `' 1000000'` | `48` | `'\nThe user is a beginner and'` | `' 1000000'` | `40` |

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

Representative probe values:

- registration:
  - `registered_k` checksum:
    - `0.0`
  - `staging_k` checksum:
    - `0.0`
- `before_load_sync`:
  - `registered_k`:
    - `same_object=false`
    - `same_data_ptr=false`
    - checksum `0.0`
    - sample `[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]`
  - `current_model_k`:
    - checksum `42.010498`
    - sample `[-0.182373, -6.851562, -6.953125, -6.921875, -6.867188, -4.375, -4.734375, -5.125]`
- `after_load_sync`:
  - `registered_k` still checksum `0.0`
  - `current_model_k` still checksum `42.010498`
- `before_save_sync`:
  - `registered_k` checksum `0.0`
  - `staging_k` checksum `0.0`
  - `current_model_k` checksum `41.992188`
- `after_save_sync`:
  - `staging_k` still checksum `0.0`

Interpretation:

- the initial experimental path had a real stale-reference bug
- the connector-visible registered/staging tensors were not following the
  current model tensors, so this first failure did not isolate the deeper
  semantic question yet

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

Representative probe values:

- `before_load_sync`:
  - `registered_k`:
    - `same_object=true`
    - `same_data_ptr=true`
    - checksum `51226.96875`
    - sample `[7.9e-05, 3846.0, 89.4375, 0.0, 2.09375, 47200.0, 89.4375, 0.0]`
  - `current_model_k`:
    - checksum `51226.96875`
    - same sample values
- `after_load_sync`:
  - `registered_k` still matched `current_model_k`
- `before_save_sync`:
  - `registered_k` checksum `51226.96875`
  - `staging_k` checksum `51226.96875`
  - `current_model_k` checksum `52823.226562`
  - `current_model_k` sample `[0.007263, 3138.0, 89.4375, 0.0, 2.34375, 49504.0, 89.4375, 0.0]`
- `after_save_sync`:
  - `staging_k` checksum `52823.226562`
  - `staging_k` sample matched the current model sample

This matters because the stale-reference repair did what it was supposed to do:

- the connector path was now following the current model tensor objects
- nonzero values were being copied into staging on save
- and yet the generation result still diverged from cold continuation

Interpretation:

- stale references were one real bug
- but they were not the root semantic issue
- after the stale-reference repair, the public `past_key_value_states`-based
  surface still did not support semantically correct external KV offload/reload

## Conclusion

The current-stack semantic investigation established the following:

- current-stack block accounting and reuse-related latency improvements were real
- the initial experimental path also had a stale-reference bug
- after repairing that bug, semantically correct external KV offload/reload was
  still not established on the current stack

The durable result is that the current-stack tensor surface used in the
experiment was not sufficient to prove semantically correct external KV
offload/reload.

## Scope Clarification

This page should be read narrowly.

What it proves:

- the tested `past_key_value_states -> staging -> loadback/sync` surface did not
  preserve semantics
- one stale-reference bug existed on that path and was repaired
- semantic mismatch still remained on that same tested surface after repair

What it does not prove:

- that every possible current-stack KV surface must fail
- that next-stack work in `vllm-spyre-next` inherits the same failure by
  default
- that `torch-spyre` cannot support a semantically correct runtime/KV contract

The broader public lesson is about proof discipline:

- semantic equality must be checked directly
- exact and partial cases both matter
- the authoritative KV/runtime surface must be stated explicitly

Related public interpretation note:

- [KV Semantic Lessons and Validation Implications (2026-03-24)](./kv-semantic-lessons-and-validation-implications-2026-03-24.md)

More concretely:

- `r17` showed that the path loaded blocks and reduced latency while still
  producing the wrong continuation text
- `r18a` showed one reason the first attempt was invalid:
  - the registered connector tensors had gone stale and remained zero while the
    current model tensors had different identities and nonzero sampled values
- `r18b` removed that stale-reference explanation:
  - the connector path then tracked the current model tensors and staging picked
    up nonzero values correctly
  - the cold-vs-reuse continuation still diverged

That is why this page treats the current `past_key_value_states` surface as not
usable for offload: even after the experimental path was repaired to follow the
current model tensors, loadback through that surface still did not preserve
generation semantics.

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
