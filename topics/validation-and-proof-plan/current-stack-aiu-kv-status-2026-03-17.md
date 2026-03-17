# Current-Stack AIU KV Status

Last updated: 2026-03-17

At a glance, the current-stack AIU KV runs show a clear reuse win across the
published benchmark sweep, with the strongest clean aligned case at just over
`2.1x` speedup. The clickable summary below is the quick skim; full run
details, parameters, commands, and the prefix-cache probe results live on the
[Current-stack AIU KV data](./current-stack-aiu-kv-data.md) page.

[![Current-stack AIU KV summary](./assets/current-stack-aiu-kv-summary-2026-03-17.png)](./current-stack-aiu-kv-data.md)

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This note is the current reporting snapshot for the AIU-backed KV work on the
current `vllm_spyre` stack.

It is meant to answer, plainly and defensibly:

- what is already proven on AIU
- what the current offload story actually is
- what remains unproven
- what is now strong enough to publish in a team status update

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
- Current-stack prefix caching on AIU is now also validated on the server path.
- The current offload story is real but limited:
  - proven: synchronous local host-backed save/load and reuse
  - not yet proven: async overlap, transport-backed offload, or serving-path TTFT benefit
- The current report-out can now include both:
  - worker-side KV reuse/offload proof
  - server-path prefix-caching proof

## What Is Proven Now

The current proof surface is the current `vllm_spyre` stack on a single AIU card.

Concretely, we have AIU-backed evidence for:

- exact-prefix aligned reuse
- partial-prefix aligned reuse
- persistent same-node service-backed KV state
- worker-side load/save accounting with zero misses in the clean aligned cases
- measurable request-latency reduction from reusing saved prompt work
- server-path prefix caching on AIU with exact and partial cases passing under the published `r16` probe

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

Representative prefix-cache server-path result:

- exact cases: `7/7` passed
- partial cases: `5/5` passed
- all cases: `True`
- exact `420`-token case:
  - expected prefix-cache hits: `320`
  - observed prefix-cache hits: `320`
  - request 1 latency: `0.097s`
  - request 2 latency: `0.028s`

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

- [`SpyreKVConnectorBridge.before_forward()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py#L79-L95)

This is the important current-stack ownership boundary:

- scheduler emits connector metadata
- worker bridge binds it
- worker initiates KV load before forward

### 2. The bridge waits for save and reports connector stats after forward

Implementation:

- [`SpyreKVConnectorBridge.after_forward()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/v1/worker/spyre_kv_connector_bridge.py#L96-L115)

That is why the current path should be described as synchronous.

### 3. The connector stores logical KV by request, layer, block, and K/V kind

Implementation:

- [`StoreKey` in `metadata.py`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/metadata.py#L32-L41)

This is the minimal logical identity that lets the current prototype be understandable.

### 4. Worker-side loads are real and accounted for explicitly

Implementation:

- [`InMemorySpyreConnector.start_load_kv()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/inmemory_spyre_connector.py#L180-L207)
- [`InMemorySpyreConnector._load_layer()`](https://github.com/toddllm/vllm-spyre/blob/06a127750d31c3c5c8fb2d8c3bd58be0ba3fa847/vllm_spyre/distributed/kv_transfer/kv_connector/v1/inmemory_spyre_connector.py#L208-L251)

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

## Prefix Caching: Why It Was Worth Doing

Current-stack prefix caching on AIU was the right complement to the KV reuse/offload slice because:

- it is a serving-path behavior, not only an offline connector behavior
- it is already grounded in the existing test surface
- it complements the connector reuse story without changing the architectural claim

Relevant existing tests:

- [`test_chunked_prefill.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_chunked_prefill.py)
- [`test_spyre_pc_scheduler_steps.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/e2e/test_spyre_pc_scheduler_steps.py)
- [`test_prefix_caching_worker.py`](https://github.com/toddllm/vllm-spyre/blob/spyre-kv-inmemory-slice/tests/v1/worker/test_prefix_caching_worker.py)

Reporting harness added for that purpose:

- [`spyre_prefix_cache_report.py`](https://github.com/toddllm/vllm-spyre/blob/8362fe718342281154af123c97ef88d2ab3353af/examples/online_inference/spyre_prefix_cache_report.py#L1-L260)

Published result:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)

One subtlety worth recording: the final published probe is `r16`, not `r14` or `r15`. The earlier attempts were useful diagnostics, but they were not suitable for report-out because:

- `r14` failed first on server startup due to missing `MASTER_ADDR`
- `r15` still launched the server with `--disable-log-stats`, which masked the prefix-cache counters even though latency shape already suggested reuse
- `r16` is the clean result with both valid probe parsing and valid server-side metrics export

Published `r16` server launch shape:

- environment:
  - `VLLM_SPYRE_DYNAMO_BACKEND=sendnn`
  - `VLLM_ENABLE_V1_MULTIPROCESSING=0`
  - `VLLM_WORKER_MULTIPROC_METHOD=spawn`
  - `MASTER_ADDR=localhost`
  - `MASTER_PORT=12355`
  - `VLLM_SERVER_DEV_MODE=1`
- server arguments:
  - `vllm serve ibm-ai-platform/micro-g3.3-8b-instruct-1b --host 127.0.0.1 --port 8000 --max-model-len 512 --max_num_seqs 4 --max_num_batched_tokens 128`
- probe arguments:
  - `examples/online_inference/spyre_prefix_cache_report.py --server-root http://127.0.0.1:8000 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --tokenizer ibm-ai-platform/micro-g3.3-8b-instruct-1b --chunk-size 128 --max-tokens 1 --warmup-prompt-tokens 32`

## Reproducibility

The report data page is intended to be fully repeatable:

- [Current-stack AIU KV data](./current-stack-aiu-kv-data.md)

That page should carry, for every published run:

- artifact name
- branch and commit
- model
- backend
- store backend
- exact task/template
- prompt and output token counts
- warmup and reuse-turn counts
- `max_num_batched_tokens`
- exact command arguments

The current reporting rule should be:

- if a number appears in the report, the matching artifact and command line should be discoverable directly from the same reporting topic

## Current Recommendation

For broader report-out:

1. publish the current-stack status with the offload story phrased carefully
2. include the AIU prefix-cache result from `r16` alongside the KV reuse/offload slice
3. keep the claims tight: current-stack proof is strong, but the full offload end-state is still not proven

The current report-out should explicitly say:

- the current stack has a real AIU-backed KV reuse/offload foundation
- the current stack also has a server-path AIU prefix-caching proof
- the offload seam is proven enough to justify further work
- the full offload end-state is not yet proven
- next-stack and multi-Spyre remain important, but they are not reasons to stall current-stack validation
