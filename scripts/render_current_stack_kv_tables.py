#!/usr/bin/env python3
"""Render GitHub-friendly tables from current-stack KV artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Markdown tables from KV reuse and prefix-cache artifacts."
    )
    parser.add_argument(
        "--benchmark-raw",
        action="append",
        default=[],
        help="Raw benchmark artifact with embedded JSON. Repeat for multiple files.",
    )
    parser.add_argument(
        "--prefix-json",
        default=None,
        help="Optional JSON summary from spyre_prefix_cache_report.py.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path.",
    )
    return parser.parse_args()


def _extract_embedded_json(raw_text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    candidate: dict[str, Any] | None = None
    for start in range(len(raw_text) - 1, -1, -1):
        if raw_text[start] != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(raw_text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "run_metadata" in payload:
            candidate = payload
            break
    if candidate is None:
        raise ValueError("No embedded JSON object found in artifact")
    return candidate


def _load_jsonish(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if path.suffix == ".json":
        return json.loads(text)
    return _extract_embedded_json(text)


def _speed_bar(speedup: float, width: int = 12) -> str:
    max_speedup = 2.0
    filled = max(0, min(width, round((speedup - 1.0) / (max_speedup - 1.0) * width)))
    return "█" * filled + "░" * (width - filled)


def _label_from_path(path: Path) -> str:
    name = path.name
    if "benchmark-" in name:
        name = name.split("benchmark-", 1)[1]
    return name.removesuffix(".raw.txt")


def _render_benchmark_section(paths: list[Path]) -> list[str]:
    runs = []
    for path in paths:
        data = _load_jsonish(path)
        comparison = data["comparisons"]["exact_reuse_vs_exact_cold"]
        runs.append((path, data, comparison))
    runs.sort(key=lambda item: float(item[2]["speedup"]), reverse=True)

    lines = [
        "## Current-Stack KV Reuse Benchmark Snapshot",
        "",
        "| Run | Template | Prompt tokens | Output tokens | Cold (s) | Reuse (s) | Speedup |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    bars: list[str] = ["```text", "Reuse speedup"]
    for path, data, comparison in runs:
        output_tokens = int(data["scenarios"]["exact_reuse"]["output_tokens"]["mean"])
        speedup = float(comparison["speedup"])
        lines.append(
            "| {run} | `{template}` | {prompt_tokens} | {output_tokens} | {cold:.3f} | {reuse:.3f} | {speedup:.3f}x |".format(
                run=_label_from_path(path),
                template=data.get("demo_template", "n/a"),
                prompt_tokens=data.get("prompt_exact_tokens", "n/a"),
                output_tokens=output_tokens,
                cold=float(comparison["cold_mean_seconds"]),
                reuse=float(comparison["reuse_mean_seconds"]),
                speedup=speedup,
            )
        )
        bars.append(f"{_label_from_path(path):<42} {_speed_bar(speedup)} {speedup:.3f}x")
    bars.append("```")
    lines.extend(["", *bars, "", "## Full Run Registry", ""])

    for path, data, comparison in runs:
        run_metadata = data.get("run_metadata", {})
        git_info = run_metadata.get("git", {})
        argv = " ".join(run_metadata.get("argv", []))
        lines.extend(
            [
                f"### `{_label_from_path(path)}`",
                "",
                f"- Artifact: `{path.name}`",
                f"- Git branch: `{git_info.get('branch', 'n/a')}`",
                f"- Git commit: `{git_info.get('commit', 'n/a')}`",
                f"- Model: `{data.get('model', 'n/a')}`",
                f"- Backend: `{data.get('backend', 'n/a')}`",
                f"- Store backend: `{data.get('store_backend', 'n/a')}`",
                f"- Template: `{data.get('demo_template', 'n/a')}`",
                f"- Task: {data.get('resolved_instruction_text', 'n/a')}",
                f"- Prompt tokens: `{data.get('prompt_exact_tokens', 'n/a')}`",
                f"- Output tokens: `{int(data['scenarios']['exact_reuse']['output_tokens']['mean'])}`",
                f"- Warmup runs: `{data.get('warmup_runs', 'n/a')}`",
                f"- Reuse turns: `{data.get('repeats', 'n/a')}`",
                f"- max_num_batched_tokens: `{data.get('effective_max_num_batched_tokens', 'n/a')}`",
                f"- Sleep between live lines: `{data.get('sleep_between_live_lines', 'n/a')}`",
                f"- Cold mean latency: `{float(comparison['cold_mean_seconds']):.6f}s`",
                f"- Reuse mean latency: `{float(comparison['reuse_mean_seconds']):.6f}s`",
                f"- Speedup: `{float(comparison['speedup']):.6f}x`",
                "",
                "Command:",
                "",
                "```bash",
                argv,
                "```",
                "",
            ]
        )
    return lines


def _render_prefix_section(prefix_json_path: Path) -> list[str]:
    data = _load_jsonish(prefix_json_path)
    run_metadata = data.get("run_metadata", {})
    git_info = run_metadata.get("git", {})
    argv = " ".join(run_metadata.get("argv", []))
    exact_cases = ", ".join(
        f"{case['prompt_len_tokens']}:{case['expected_hit_tokens']}"
        for case in data["exact_cases"]
    )
    partial_cases = ", ".join(
        f"{case['prompt_len_tokens']}:{case['expected_hit_tokens']}"
        for case in data["partial_cases"]
    )
    lines = [
        "## Prefix Cache Probe Snapshot",
        "",
        f"- Artifact: `{prefix_json_path.name}`",
        f"- Git branch: `{git_info.get('branch', 'n/a')}`",
        f"- Git commit: `{git_info.get('commit', 'n/a')}`",
        f"- Model: `{data['model']}`",
        f"- Tokenizer: `{data.get('tokenizer', 'n/a')}`",
        f"- Chunk size: `{data['chunk_size']}`",
        f"- Max new tokens: `{data.get('max_tokens', 'n/a')}`",
        f"- Warmup prompt tokens: `{data.get('warmup_prompt_tokens', 'n/a')}`",
        f"- Exact cases: `{exact_cases}`",
        f"- Partial cases: `{partial_cases}`",
        f"- All cases passed: `{data['summary']['all_passed']}`",
        "",
        "### Exact Prefix Cases",
        "",
        "| Prompt tokens | Expected hits | Observed hits | Query tokens | Req 1 (s) | Req 2 (s) | Pass |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for case in data["exact_cases"]:
        lines.append(
            "| {prompt_len_tokens} | {expected_hit_tokens} | {observed_hit_tokens} | "
            "{observed_query_tokens} | {req1:.3f} | {req2:.3f} | {passed} |".format(
                prompt_len_tokens=case["prompt_len_tokens"],
                expected_hit_tokens=case["expected_hit_tokens"],
                observed_hit_tokens=case["observed_hit_tokens"],
                observed_query_tokens=case["observed_query_tokens"],
                req1=case["first_request"]["latency_seconds"],
                req2=case["second_request"]["latency_seconds"],
                passed="yes" if case["pass"] else "no",
            )
        )

    lines.extend(
        [
            "",
            "### Partial Prefix Cases",
            "",
            "| Prompt tokens | Second prompt tokens | Expected hits | Observed hits | Query tokens | Req 1 (s) | Req 2 (s) | Pass |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
        ]
    )
    for case in data["partial_cases"]:
        lines.append(
            "| {prompt_len_tokens} | {second_prompt_len_tokens} | {expected_hit_tokens} | "
            "{observed_hit_tokens} | {observed_query_tokens} | {req1:.3f} | {req2:.3f} | {passed} |".format(
                prompt_len_tokens=case["prompt_len_tokens"],
                second_prompt_len_tokens=case["second_prompt_len_tokens"],
                expected_hit_tokens=case["expected_hit_tokens"],
                observed_hit_tokens=case["observed_hit_tokens"],
                observed_query_tokens=case["observed_query_tokens"],
                req1=case["first_request"]["latency_seconds"],
                req2=case["second_request"]["latency_seconds"],
                passed="yes" if case["pass"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "Command:",
            "",
            "```bash",
            argv,
            "```",
        ]
    )
    return lines


def main() -> int:
    args = parse_args()
    benchmark_paths = [Path(path) for path in args.benchmark_raw]
    lines: list[str] = ["# Current-Stack AIU KV Data", ""]
    if benchmark_paths:
        lines.extend(_render_benchmark_section(benchmark_paths))
    if args.prefix_json:
        lines.extend(["", * _render_prefix_section(Path(args.prefix_json))])

    markdown = "\n".join(lines).rstrip() + "\n"
    print(markdown)
    if args.output:
        Path(args.output).write_text(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
