# Current-Stack AIU KV Status

Last updated: 2026-03-17

The current `vllm_spyre` AIU benchmark sweep shows a consistent KV reuse
benefit across the published runs. Full run-by-run parameters, commands, and
prefix-cache probe results are on the
[Current-stack AIU KV data](./current-stack-aiu-kv-data.md) page.

[![Current-stack AIU KV summary](./assets/current-stack-aiu-kv-summary-2026-03-17.png)](./current-stack-aiu-kv-data.md)

## Scope

- Stack: current `vllm_spyre`
- Hardware scope: single AIU card
- Included here:
  - worker-side KV reuse results
  - service-backed same-node KV persistence results
  - server-path prefix-caching results
- Not included here:
  - `vllm-spyre-next`
  - multi-Spyre scale-out
  - transport-backed prefill/decode disaggregation

Related pages:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)
- [Validation and Proof Plan](./README.md)
- [KV Offload](../kv-offload/README.md)
- [KV Reuse](../kv-reuse/README.md)
- [Prefill/Decode Disaggregation](../prefill-decode-disaggregation/README.md)
- [Top-level index](../../README.md)

## Current Status

- Exact aligned KV reuse is working on AIU.
- Partial aligned KV reuse is working on AIU.
- Same-node service-backed KV persistence is working on AIU.
- Server-path prefix caching is working on AIU.
- The current results support synchronous local host-backed KV save/load/reuse.

## Representative Results

### KV reuse benchmark

- Strongest published clean aligned case:
  - run: `r6l-exact-live-shm-service`
  - prompt tokens: `384`
  - output tokens: `1`
  - cold mean latency: `0.142s`
  - reuse mean latency: `0.067s`
  - speedup: `2.113x`
- Longer generated outputs reduce the measured speedup, as expected:
  - `r11`: `1.649x` at `448` prompt tokens and `8` output tokens
  - `r12a`: `1.360x` at `448` prompt tokens and `16` output tokens
  - `r12d`: `1.124x` at `448` prompt tokens and `48` output tokens

Full benchmark tables:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md#current-stack-kv-reuse-benchmark-snapshot)

### Prefix caching

- Published probe: `r16`
- Exact cases passed: `7/7`
- Partial cases passed: `5/5`
- All cases passed: `True`
- Representative exact case:
  - prompt tokens: `420`
  - expected hits: `320`
  - observed hits: `320`
  - request 1 latency: `0.097s`
  - request 2 latency: `0.028s`

Full prefix-cache tables:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md#prefix-cache-probe-snapshot)

## Offload Status

### Confirmed in the current report

- KV can be staged out of the active execution context.
- KV can be saved in a host-backed medium.
- Later work can reload compatible KV and continue.
- The current implementation produces measurable latency benefit on AIU.

### Not yet demonstrated in the current report

- Async overlap with forward
- DMA-overlap benefit as a published result
- Transport-backed local offload as the standard path
- Cross-process or cross-engine transfer as the standard path
- Serving-path TTFT improvement from offload
- Transport-backed prefill/decode disaggregation

### Precise statement

- Confirmed: synchronous local host-backed KV save/load/reuse on the current stack
- Not yet confirmed: transport-backed or overlap-backed offload as a serving feature

## Relevant Implementation References

### Worker-side load and save boundary

- [`SpyreKVConnectorBridge.before_forward()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py#L79-L95)
- [`SpyreKVConnectorBridge.after_forward()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py#L96-L115)

### Logical KV identity

- [`StoreKey` in `metadata.py`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/metadata.py#L32-L41)

### Explicit worker-side loads

- [`InMemorySpyreConnector.start_load_kv()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/inmemory_spyre_connector.py#L180-L207)
- [`InMemorySpyreConnector._load_layer()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/inmemory_spyre_connector.py#L208-L251)

### Prefix-cache reporting harness

- [`spyre_prefix_cache_report.py`](https://github.com/toddllm/vllm-spyre/blob/8362fe718342281154af123c97ef88d2ab3353af/examples/online_inference/spyre_prefix_cache_report.py#L1-L260)
- [`test_chunked_prefill.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_chunked_prefill.py)
- [`test_spyre_pc_scheduler_steps.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_spyre_pc_scheduler_steps.py)
- [`test_prefix_caching_worker.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/v1/worker/test_prefix_caching_worker.py)

## Reproducibility

The companion data page records, for each published run:

- artifact name
- branch
- commit
- model
- backend
- store backend
- template or task
- prompt and output token counts
- warmup and reuse-turn counts
- `max_num_batched_tokens`
- command arguments

See:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)

## Immediate Next Steps

- Keep the current-stack report limited to the confirmed claims above.
- Use the current-stack results as the baseline for future offload and
  disaggregation work.
- Track next-stack and multi-Spyre work separately from this report.
