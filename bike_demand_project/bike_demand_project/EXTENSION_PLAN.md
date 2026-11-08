# Exploratory extension plan

The original test results have already been examined. These additions are
exploratory diagnostics, not a new untouched-test confirmation. The original
model selection, predictions and headline remain unchanged.

1. Add history-only Ridge using the six existing history inputs, the same three
   60-day expanding validation folds and alpha grid [0.1, 1, 10, 100]. Choose alpha
   on development data. Compare it with the original calendar-only and combined
   Ridge. Report fold results and the existing final test, labeled exploratory.
2. Paired circular-block bootstrap of baseline/Ridge daily absolute errors.
   Primary block length 7 days; sensitivity lengths 3 and 14. Generate 10,000
   resamples per length, seed 20261106 + block length. Use the same sampled dates
   for both methods. Report percentile 95% intervals for absolute MAE reduction
   and 100*(1 - resampled Ridge MAE/resampled baseline MAE). This assumes local
   dependence is represented by blocks and approximately stable error behavior.
   A short, seasonally changing test period limits that approximation. The
   intervals are conditional on the fitted models and this period, and exclude
   training/model-selection uncertainty. They are not forecast intervals.
3. Audit the original Ridge errors by month, weekend and prior volatility.
   Volatility = prior 7-day sample standard deviation / prior 7-day mean.
   Flag a day when this exceeds the development-data 75th percentile. For each
   development validation fold, compute its threshold on that fold's training
   rows only. Do not search for a threshold that looks favorable on test.
4. Research context for Sandy and late-December failures. Preserve all days in
   the headline metrics. Treat weather and closure context as explanatory
   evidence, not new model inputs or proof of causality.
5. Produce an editable slide deck with methods, results, uncertainty, failures,
   limitations and sources. No new claimed operational savings.
