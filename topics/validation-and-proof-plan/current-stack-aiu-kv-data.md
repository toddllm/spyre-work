# Current-Stack AIU KV Data

## Current-Stack KV Reuse Benchmark Snapshot

| Run | Template | Prompt tokens | Output tokens | Cold (s) | Reuse (s) | Speedup |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| r6l-exact-live-shm-service | `n/a` | 384 | 1 | 0.142 | 0.067 | 2.113x |
| r11-exact-chicken-soup-demo | `chicken_soup` | 448 | 8 | 0.334 | 0.203 | 1.649x |
| r12a-exact-chicken-soup-p448-o16 | `chicken_soup` | 448 | 16 | 0.436 | 0.321 | 1.360x |
| r12b-exact-chicken-soup-p448-o24 | `chicken_soup` | 448 | 24 | 0.574 | 0.454 | 1.265x |
| r12c-exact-chicken-soup-p448-o32 | `chicken_soup` | 448 | 32 | 0.699 | 0.600 | 1.164x |
| r12d-exact-chicken-soup-p448-o48 | `chicken_soup` | 448 | 48 | 0.945 | 0.840 | 1.124x |
| r13e-exact-power-query-columns-p384-o16 | `power_query_columns` | 384 | 16 | 0.425 | 0.319 | 1.332x |

```text
Reuse speedup
r6l-exact-live-shm-service                 ████████████ 2.113x
r11-exact-chicken-soup-demo                ████████░░░░ 1.649x
r12a-exact-chicken-soup-p448-o16           ████░░░░░░░░ 1.360x
r12b-exact-chicken-soup-p448-o24           ███░░░░░░░░░ 1.265x
r12c-exact-chicken-soup-p448-o32           ██░░░░░░░░░░ 1.164x
r12d-exact-chicken-soup-p448-o48           █░░░░░░░░░░░ 1.124x
r13e-exact-power-query-columns-p384-o16    ████░░░░░░░░ 1.332x
```
