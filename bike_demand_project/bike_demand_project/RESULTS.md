# First locked experiment: results

Ridge was selected using earlier validation windows, then reduced mean absolute
error by 35.6% against the same-weekday-last-week baseline on the 92-day final test.

| Method | Validation MAE | Final test MAE | Test RMSE |
|---|---:|---:|---:|
| Same weekday last week | 976.24 | 1457.59 | 2047.17 |
| Ridge, calendar + history | 732.31 | 938.97 | 1379.68 |
| Gradient boosting | 1117.64 | 1374.16 | 1887.31 |
| Calendar-only Ridge (explanatory) | 863.67 | 1323.56 | 1869.50 |

Errors are rental counts per day. Validation values are averages across three
60-day folds, not training scores. Lower is better.

The Ridge model is a weighted combination of calendar and recent-history inputs,
with a penalty that discourages unstable coefficients. The more flexible boosting
candidate did not outperform it. The comparison with calendar-only Ridge suggests
that recent rental history helps in this experiment; it is not a causal result.

The model still missed October 29 badly: 5862 predicted rentals versus 22 recorded.
This day remains in all reported test scores. The data alone do not establish the
cause. Weekday MAE was 837; weekend MAE was 1197. Average improvement does not mean
reliable predictions on every day.

This is a historical backtest, assuming complete yesterday totals are available
before each forecast. It is not a production forecast or an estimate of savings.
Do not tune further on the final test without calling the changes exploratory.

Verification: all nine notebook code cells executed; checks for continuity,
missing values, duplicate dates, count consistency and temporal leakage passed.
Saved MAE values were independently recomputed from the per-day prediction file.


## Exploratory additions

The original test had already been inspected when these additions were designed.
They do not change the original selected model or any original predictions.

| Ridge inputs | Validation MAE | Final test MAE |
|---|---:|---:|
| Calendar only | 863.67 | 1323.56 |
| History only | 727.46 | 919.58 |
| Calendar + history | 732.31 | 938.97 |

History carries much of the predictive signal. The combined and history-only
versions perform similarly; the evidence does not establish an advantage for
adding calendar features to history. Each version selects its penalty on the
same development folds, without using final test scores.

A paired circular block bootstrap (10,000 draws, seven-day blocks) gives an
approximate 95% percentile interval of **21.1%–49.7%** for the original model's
35.6% reduction in MAE relative to last week. Three- and fourteen-day block
sensitivity intervals remain above zero. These intervals condition on the fitted
models and short, seasonally changing test period. They are not prediction
intervals and exclude training and model-selection uncertainty.

A flag based on high volatility in the previous seven days identifies 27 test
dates with MAE 1100.15, versus 872.02 on the other 65 dates. The threshold uses
only development data. Development-validation flagged dates have MAE 1032.57
(n=13), versus 708.94 (n=167), with fold-specific training thresholds. This is a
descriptive diagnostic, not an independently validated risk model. It misses
the first Sandy shutdown day.

Contemporaneous reporting documents an approximately 36-hour Bikeshare shutdown
during Sandy. NWS records supply weather context for December misses. These
sources support interpretation but do not identify causal effects or explain
every recorded count. See `EVENT_CONTEXT.md` for links and qualifications.
All dates remain in the scores.

Verification: the original four frozen output files retain their SHA-256 hashes;
the combined Ridge predictions are exactly reproduced. Extension checks,
per-day predictions, grouped errors and bootstrap draws are included.
