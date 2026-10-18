# Benchmark comparison

Baseline: Python 3.11.16, `uv run python scripts/benchmark.py 1000`, five repeats per workload. Each timed call verifies its rendered output. Timings are seconds for 1,000 renders, not test gates.

| Workload | Baseline repeats |
| --- | --- |
| ordinary | 0.021116, 0.020679, 0.021045, 0.020899, 0.020735 |
| explicit-empty | 0.022463, 0.022882, 0.022850, 0.022382, 0.022914 |
| partial | 0.004432, 0.004473, 0.004299, 0.004492, 0.004433 |
| compat-permissive | 0.005021, 0.005006, 0.005168, 0.005196, 0.005180 |
| function-permissive | 0.004906, 0.004875, 0.004918, 0.004722, 0.004726 |
| section-permissive | 0.006149, 0.006013, 0.006280, 0.006314, 0.006308 |
| nested-callback-permissive | 0.008163, 0.008229, 0.007942, 0.008154, 0.008388 |
| compat-explicit | 0.005050, 0.005245, 0.004969, 0.005099, 0.005080 |
| function-explicit | 0.004860, 0.004616, 0.004872, 0.004886, 0.004839 |
| section-explicit | 0.006132, 0.006348, 0.006228, 0.006531, 0.006265 |
| nested-callback-explicit | 0.008359, 0.008321, 0.008377, 0.008290, 0.008132 |

## Refactored engine

Same Python environment and workloads, run using `.venv/bin/python scripts/benchmark.py 1000` (uv's cache directory required elevated access in the sandbox). All output assertions passed.

| Workload | Refactored repeats |
| --- | --- |
| ordinary | 0.018514, 0.018419, 0.018494, 0.018618, 0.017656 |
| explicit-empty | 0.020839, 0.020767, 0.020210, 0.020335, 0.020999 |
| partial | 0.004141, 0.004026, 0.004188, 0.004022, 0.004114 |
| compat-permissive | 0.005186, 0.005155, 0.004934, 0.004943, 0.004872 |
| function-permissive | 0.004190, 0.004128, 0.004167, 0.004257, 0.004120 |
| section-permissive | 0.005694, 0.005523, 0.005683, 0.005540, 0.005748 |
| nested-callback-permissive | 0.007889, 0.007554, 0.007581, 0.007582, 0.007651 |
| compat-explicit | 0.005197, 0.005165, 0.005257, 0.005315, 0.005231 |
| function-explicit | 0.004550, 0.004418, 0.004559, 0.004372, 0.004509 |
| section-explicit | 0.005835, 0.005994, 0.005893, 0.005912, 0.005835 |
| nested-callback-explicit | 0.007787, 0.007839, 0.007758, 0.007902, 0.007748 |

Median ordinary rendering was approximately 12% faster in this comparison; explicit compatibility callbacks were approximately 3% slower. Earlier post-refactor runs showed larger callback overhead, so these short local timings should not be treated as a universal speed claim. No timing threshold was added to tests.
