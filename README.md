# HPC Data-Structure Optimization Prototype

This reproducible Python prototype compares repeated membership testing with:

- a baseline `list` (linear search, expected O(n) per query), and
- an optimized `set` (hash lookup, expected O(1) average per query).

## Run

```bash
python3 membership_benchmark.py
```

The script validates identical results, reports median timings over five runs,
and writes `results/benchmark_results.csv`. Use the same Python interpreter and
an otherwise idle machine when comparing runs. Timing values are specific to
the machine; the scaling trend is the important result.
# MSCS532_FinalProjectPart1
# MSCS532_FinalProjectPart1
# MSCS532_FinalProjectPart1
