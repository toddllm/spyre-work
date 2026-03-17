# Current-Stack AIU KV Status

Last updated: 2026-03-17

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This note is the current reporting snapshot for the AIU-backed KV work on the
current `vllm_spyre` stack.

It is meant to answer, plainly and defensibly:

- what is already proven on AIU
- what the current offload story actually is
- what remains unproven
- what one more critical-path validation is worth doing before broader report-out

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Tactical watch list: [../../LIVE_TRACKER.md](../../LIVE_TRACKER.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [KV Reuse](../kv-reuse/README.md)
- Neighbor topic: [KV Offload](../kv-offload/README.md)
- Neighbor topic: [Prefill/Decode Disaggregation](../prefill-decode-disaggregation/README.md)

</details>

## Executive Summary

- The current `vllm_spyre` path now has a real AIU-backed KV reuse proof.
- Exact aligned reuse and partial aligned reuse both work through the worker-side connector path.
- Service-backed host persistence works on AIU and produces measurable request-latency benefit.
- The current offload story is real but limited:
  - proven: synchronous local host-backed save/load and reuse
  - not yet proven: async overlap, transport-backed offload, or serving-path TTFT benefit
- The next useful validation before broader report-out is current-stack prefix caching on AIU, because it is closer to user-visible serving semantics than more demo tuning.

## What Is Proven Now

The current proof surface is the current `vllm_spyre` stack on a single AIU card.

Concretely, we have AIU-backed evidence for:

- exact-prefix aligned reuse
- partial-prefix aligned reuse
- persistent same-node service-backed KV state
- worker-side load/save accounting with zero misses in the clean aligned cases
- measurable request-latency reduction from reusing saved prompt work

Representative exact aligned result:

- warm baseline: about `0.142s`
- exact reuse: about `0.069s` then `0.065s`
- speedup: about `2.05x` to `2.18x`

Representative longer request boundary runs showed the expected tradeoff:

- more generated output makes the demo more legible
- but decode cost progressively eats the prefill-side reuse win

That was useful as a boundary check, but it is no longer the main source of understanding.

For current benchmark tables, see:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)

## The Offload Story From First Principles

### Reuse, offload, and disaggregation are different

They are related, but they are not the same milestone.

```text
reuse
  -> trust existing compatible KV and continue execution

offload
  -> save KV out of the active execution context and later reload it

prefill/decode disaggregation
  -> transfer KV between distinct producer and consumer execution contexts
```

### What is proven today

What is proven today is a current-stack, worker-side, host-backed slice:

- KV is staged out of the active execution context
- KV is saved in a host-backed medium
- later work can reload compatible KV and continue
- this produces measurable latency benefit on AIU

That is enough to say the current worker/model-runner seam is viable for real progress.

### What is not yet proven

We do **not** yet have a full end-state offload proof.

Not yet proven:

- async overlap with forward
- true DMA-style transfer benefit
- transport-backed local offload as the standing path
- cross-process or cross-engine transfer as the normal path
- serving-path TTFT improvement
- PD disaggregation over transport

So the precise statement is:

- **proved:** local host-backed KV reuse/offload mechanics on the current stack
- **not yet proved:** transport-backed or overlap-backed KV offload as a serving feature

That distinction matters and should stay explicit in any report-out.

## Code-Level Seams

The key point is that the current offload/reuse seam is worker-side and staging-based.

### 1. The bridge binds scheduler metadata and loads before forward

Implementation:

- [`spyre_kv_connector_bridge.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py)

Small excerpt:

```python
self._kv_connector.bind_connector_metadata(
    scheduler_output.kv_connector_metadata
)
self._kv_connector.start_load_kv(get_forward_context())
```

This is the important current-stack ownership boundary:

- scheduler emits connector metadata
- worker bridge binds it
- worker initiates KV load before forward

### 2. The bridge waits for save and reports connector stats after forward

Implementation:

- [`spyre_kv_connector_bridge.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py)

Small excerpt:

```python
if wait_for_save:
    self._kv_connector.wait_for_save()

output.kv_connector_stats = self._kv_connector.get_kv_connector_stats()
```

That is why the current path should be described as synchronous.

### 3. The connector stores logical KV by request, layer, block, and K/V kind

Implementation:

- [`metadata.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/distributed/kv_transfer/kv_connector/v1/metadata.py)

Small excerpt:

```python
@dataclass(frozen=True)
class StoreKey:
    req_id: str
    layer_idx: int
    block_id: int
    kv_kind: KVKind
```

This is the minimal logical identity that lets the current prototype be understandable.

### 4. Worker-side loads are real and accounted for explicitly

Implementation:

- [`inmemory_spyre_connector.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/vllm_spyre/distributed/kv_transfer/kv_connector/v1/inmemory_spyre_connector.py)

Small excerpt:

```python
for layer_idx, layer_name in enumerate(self._layer_names):
    layer_load, layer_miss = self._load_layer(meta, layer_idx, layer_name)
    total_load += layer_load
    total_miss += layer_miss
```

This is the code-level reason the current claim is stronger than “we think reuse is happening.”

## Why The Current Stack Is Still The Right Proof Surface

The current stack is still the right place for the first serious AIU proof because:

- the real worker/model-runner seam already exists
- staged/live KV synchronization already exists
- the proof burden is single-card semantics, not long-term elegance

By contrast, `vllm-spyre-next` is still carrying more substrate risk:

- wrapped-layer work
- attention backend maturity
- upstream test-framework integration
- torch-spyre device/copy/stream/runtime maturity

That is why the current reporting stance should remain:

- prove value on the current stack now
- keep the next stack moving as the long-term destination
- do not block current-stack proof work on next-stack maturity

## Prefix Caching: The One More Useful Validation

The next critical-path validation is current-stack prefix caching on AIU.

Why this is worth doing now:

- it is a serving-path behavior, not only an offline connector behavior
- it is already grounded in the existing test surface
- it complements the connector reuse story without changing the architectural claim

Relevant existing tests:

- [`test_chunked_prefill.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_chunked_prefill.py)
- [`test_spyre_pc_scheduler_steps.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_spyre_pc_scheduler_steps.py)
- [`test_prefix_caching_worker.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/v1/worker/test_prefix_caching_worker.py)

Reporting harness added for that purpose:

- [`spyre_prefix_cache_report.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/examples/online_inference/spyre_prefix_cache_report.py)

Once the AIU prefix-cache artifact is copied back, the results should be folded into:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)

## Current Recommendation

Before broader report-out:

1. run the AIU prefix-cache probe
2. update the tables in the validation topic
3. publish the current-stack status with the offload story phrased carefully

The current report-out should explicitly say:

- the current stack has a real AIU-backed KV reuse/offload foundation
- the offload seam is proven enough to justify further work
- the full offload end-state is not yet proven
- next-stack and multi-Spyre remain important, but they are not reasons to stall current-stack validation
