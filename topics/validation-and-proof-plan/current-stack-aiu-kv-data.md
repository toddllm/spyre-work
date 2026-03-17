# Current-Stack AIU KV Data

## Current-Stack KV Reuse Benchmark Snapshot

| Run | Template | Prompt tokens | Output tokens | Cold (s) | Reuse (s) | Speedup |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| r6l-exact-live-shm-service | `n/a` | 384 | 1 | 0.142 | 0.067 | 2.113x |
| r11-exact-chicken-soup-demo | `chicken_soup` | 448 | 8 | 0.334 | 0.203 | 1.649x |
| r12a-exact-chicken-soup-p448-o16 | `chicken_soup` | 448 | 16 | 0.436 | 0.321 | 1.360x |
| r13e-exact-power-query-columns-p384-o16 | `power_query_columns` | 384 | 16 | 0.425 | 0.319 | 1.332x |
| r12b-exact-chicken-soup-p448-o24 | `chicken_soup` | 448 | 24 | 0.574 | 0.454 | 1.265x |
| r12c-exact-chicken-soup-p448-o32 | `chicken_soup` | 448 | 32 | 0.699 | 0.600 | 1.164x |
| r12d-exact-chicken-soup-p448-o48 | `chicken_soup` | 448 | 48 | 0.945 | 0.840 | 1.124x |

```text
Reuse speedup
r6l-exact-live-shm-service                 ████████████ 2.113x
r11-exact-chicken-soup-demo                ████████░░░░ 1.649x
r12a-exact-chicken-soup-p448-o16           ████░░░░░░░░ 1.360x
r13e-exact-power-query-columns-p384-o16    ████░░░░░░░░ 1.332x
r12b-exact-chicken-soup-p448-o24           ███░░░░░░░░░ 1.265x
r12c-exact-chicken-soup-p448-o32           ██░░░░░░░░░░ 1.164x
r12d-exact-chicken-soup-p448-o48           █░░░░░░░░░░░ 1.124x
```

## Full Run Registry

### `r6l-exact-live-shm-service`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r6l-exact-live-shm-service.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `679f30dabe1159eccfad402e56d0899339a55696`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `n/a`
- Task: n/a
- Prompt tokens: `384`
- Output tokens: `1`
- Warmup runs: `1`
- Reuse turns: `2`
- max_num_batched_tokens: `128`
- Sleep between live lines: `n/a`
- Cold mean latency: `0.141818s`
- Reuse mean latency: `0.067101s`
- Speedup: `2.113491x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --shared-prefix-tokens 384 --partial-tail-tokens 16 --max-num-batched-tokens 128 --max-new-tokens 1 --repeats 2 --print-live
```

### `r11-exact-chicken-soup-demo`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r11-exact-chicken-soup-demo.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `73acbad01abbc9aad8abf531f7ced9eae2c79f09`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `chicken_soup`
- Task: Provide a list of instructions for preparing chicken soup.
- Prompt tokens: `448`
- Output tokens: `8`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.334093s`
- Reuse mean latency: `0.202601s`
- Speedup: `1.649014x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template chicken_soup --demo-prompt-tokens 448 --demo-response-tokens 8 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 160 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```

### `r12a-exact-chicken-soup-p448-o16`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r12a-exact-chicken-soup-p448-o16.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `db085ea8c9c85b439fa3ce83e8f5a49a2cbc8307`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `chicken_soup`
- Task: Provide a list of instructions for preparing chicken soup.
- Prompt tokens: `448`
- Output tokens: `16`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.436128s`
- Reuse mean latency: `0.320653s`
- Speedup: `1.360125x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template chicken_soup --demo-prompt-tokens 448 --demo-response-tokens 16 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 220 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```

### `r13e-exact-power-query-columns-p384-o16`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r13e-exact-power-query-columns-p384-o16.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `db085ea8c9c85b439fa3ce83e8f5a49a2cbc8307`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `power_query_columns`
- Task: Explain how to add multiple new columns in M for Power Query or Power BI.
- Prompt tokens: `384`
- Output tokens: `16`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.424788s`
- Reuse mean latency: `0.318996s`
- Speedup: `1.331640x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template power_query_columns --demo-prompt-tokens 384 --demo-response-tokens 16 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 220 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```

### `r12b-exact-chicken-soup-p448-o24`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r12b-exact-chicken-soup-p448-o24.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `db085ea8c9c85b439fa3ce83e8f5a49a2cbc8307`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `chicken_soup`
- Task: Provide a list of instructions for preparing chicken soup.
- Prompt tokens: `448`
- Output tokens: `24`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.574027s`
- Reuse mean latency: `0.453768s`
- Speedup: `1.265024x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template chicken_soup --demo-prompt-tokens 448 --demo-response-tokens 24 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 220 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```

### `r12c-exact-chicken-soup-p448-o32`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r12c-exact-chicken-soup-p448-o32.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `db085ea8c9c85b439fa3ce83e8f5a49a2cbc8307`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `chicken_soup`
- Task: Provide a list of instructions for preparing chicken soup.
- Prompt tokens: `448`
- Output tokens: `32`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.698658s`
- Reuse mean latency: `0.600246s`
- Speedup: `1.163953x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template chicken_soup --demo-prompt-tokens 448 --demo-response-tokens 32 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 220 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```

### `r12d-exact-chicken-soup-p448-o48`

- Artifact: `2026-03-17-aiu-sendnn-benchmark-r12d-exact-chicken-soup-p448-o48.raw.txt`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `db085ea8c9c85b439fa3ce83e8f5a49a2cbc8307`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Backend: `sendnn`
- Store backend: `serialized_shared_memory_service`
- Template: `chicken_soup`
- Task: Provide a list of instructions for preparing chicken soup.
- Prompt tokens: `448`
- Output tokens: `48`
- Warmup runs: `1`
- Reuse turns: `4`
- max_num_batched_tokens: `128`
- Sleep between live lines: `1.25`
- Cold mean latency: `0.944599s`
- Reuse mean latency: `0.840227s`
- Speedup: `1.124219x`

Command:

```bash
examples/offline_inference/spyre_kv_reuse_benchmark.py --backend sendnn --store-backend serialized_shared_memory_service --service-socket /tmp/spyre-kv-persistent.sock --clear-service --demo-mode warm_baseline_then_reuse --warmup-runs 1 --live-output-style demo --demo-template chicken_soup --demo-prompt-tokens 448 --demo-response-tokens 48 --demo-turns 4 --demo-pause-seconds 1.25 --demo-show-text --demo-prompt-preview-chars 180 --demo-answer-preview-chars 220 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --aligned-prompts --exact-only --max-num-batched-tokens 128 --print-live
```


## Prefix Cache Probe Snapshot

- Artifact: `2026-03-17-aiu-prefix-cache-r16.json`
- Git branch: `spyre-kv-inmemory-slice`
- Git commit: `8362fe718342281154af123c97ef88d2ab3353af`
- Model: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Tokenizer: `ibm-ai-platform/micro-g3.3-8b-instruct-1b`
- Chunk size: `128`
- Max new tokens: `1`
- Warmup prompt tokens: `32`
- Exact cases: `53:0, 127:0, 144:64, 250:128, 299:192, 350:256, 420:320`
- Partial cases: `144:0, 250:0, 299:64, 350:128, 420:192`
- All cases passed: `True`

### Exact Prefix Cases

| Prompt tokens | Expected hits | Observed hits | Query tokens | Req 1 (s) | Req 2 (s) | Pass |
| ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 53 | 0 | 0 | 106 | 0.030 | 0.026 | yes |
| 127 | 0 | 0 | 254 | 0.025 | 0.026 | yes |
| 144 | 64 | 64 | 288 | 0.052 | 0.026 | yes |
| 250 | 128 | 128 | 500 | 0.052 | 0.029 | yes |
| 299 | 192 | 192 | 598 | 0.080 | 0.028 | yes |
| 350 | 256 | 256 | 700 | 0.073 | 0.027 | yes |
| 420 | 320 | 320 | 840 | 0.097 | 0.028 | yes |

### Partial Prefix Cases

| Prompt tokens | Second prompt tokens | Expected hits | Observed hits | Query tokens | Req 1 (s) | Req 2 (s) | Pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 144 | 16 | 0 | 0 | 160 | 0.047 | 0.025 | yes |
| 250 | 122 | 0 | 0 | 372 | 0.049 | 0.025 | yes |
| 299 | 171 | 64 | 64 | 470 | 0.072 | 0.026 | yes |
| 350 | 222 | 128 | 128 | 572 | 0.075 | 0.027 | yes |
| 420 | 292 | 192 | 192 | 712 | 0.096 | 0.027 | yes |

Command:

```bash
examples/online_inference/spyre_prefix_cache_report.py --server-root http://127.0.0.1:8000 --model ibm-ai-platform/micro-g3.3-8b-instruct-1b --tokenizer ibm-ai-platform/micro-g3.3-8b-instruct-1b --chunk-size 128 --max-tokens 1 --warmup-prompt-tokens 32 --json-out lab-artifacts/spyre-kv-inmemory-slice/2026-03-17-aiu-prefix-cache-r16.json --markdown-out lab-artifacts/spyre-kv-inmemory-slice/2026-03-17-aiu-prefix-cache-r16.md
```
