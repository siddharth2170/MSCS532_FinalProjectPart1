#!/usr/bin/env python3
"""Benchmark repeated membership queries using a list versus a hash set.

The workload models an HPC preprocessing stage that repeatedly checks whether
particle/node identifiers belong to an active subset. Both implementations
produce identical hit counts; only the lookup data structure changes.
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Result:
    size: int
    queries: int
    list_seconds: float
    set_build_seconds: float
    set_query_seconds: float
    speedup_query_only: float
    speedup_end_to_end: float
    list_bytes: int
    set_bytes: int
    hits: int


def timed(function, repeats: int) -> tuple[float, int]:
    """Return median elapsed seconds and the function's integer result."""
    samples: list[float] = []
    result = 0
    for _ in range(repeats):
        start = time.perf_counter_ns()
        result = function()
        samples.append((time.perf_counter_ns() - start) / 1_000_000_000)
    return statistics.median(samples), result


def benchmark(size: int, query_count: int, repeats: int, seed: int) -> Result:
    rng = random.Random(seed + size)
    active_ids = rng.sample(range(size * 10), size)
    # Half hits and half misses, shuffled to avoid a favorable access pattern.
    queries = rng.sample(active_ids, query_count // 2)
    queries += rng.sample(range(size * 10, size * 20), query_count - len(queries))
    rng.shuffle(queries)

    list_time, list_hits = timed(
        lambda: sum(identifier in active_ids for identifier in queries), repeats
    )

    build_samples: list[float] = []
    active_set: set[int] = set()
    for _ in range(repeats):
        start = time.perf_counter_ns()
        active_set = set(active_ids)
        build_samples.append((time.perf_counter_ns() - start) / 1_000_000_000)
    build_time = statistics.median(build_samples)
    set_time, set_hits = timed(
        lambda: sum(identifier in active_set for identifier in queries), repeats
    )

    if list_hits != set_hits:
        raise AssertionError("Optimized and baseline implementations disagree")

    return Result(
        size=size,
        queries=query_count,
        list_seconds=list_time,
        set_build_seconds=build_time,
        set_query_seconds=set_time,
        speedup_query_only=list_time / set_time,
        speedup_end_to_end=list_time / (build_time + set_time),
        list_bytes=sys.getsizeof(active_ids),
        set_bytes=sys.getsizeof(active_set),
        hits=set_hits,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[1_000, 5_000, 10_000, 25_000])
    parser.add_argument("--queries", type=int, default=2_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--csv", type=Path, default=Path("results/benchmark_results.csv"))
    args = parser.parse_args()

    results = [benchmark(n, min(args.queries, n), args.repeats, args.seed) for n in args.sizes]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Result.__dataclass_fields__))
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)

    print(f"{'N':>8} {'Q':>6} {'list (ms)':>11} {'set query (ms)':>15} {'build (ms)':>11} {'speedup':>10}")
    for r in results:
        print(f"{r.size:8,d} {r.queries:6,d} {r.list_seconds*1e3:11.3f} "
              f"{r.set_query_seconds*1e3:15.3f} {r.set_build_seconds*1e3:11.3f} "
              f"{r.speedup_end_to_end:9.1f}x")


if __name__ == "__main__":
    main()
