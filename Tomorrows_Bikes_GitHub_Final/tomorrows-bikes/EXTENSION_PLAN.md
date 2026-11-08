# Exploratory analysis design

These analyses were designed after the original test results had been examined.
They help explain the result and its limitations, while leaving the original
selection, predictions, and headline score unchanged.

## Comparing feature groups

The feature comparison adds a history-only Ridge model to the original
calendar-only and combined versions. It uses the same six history features,
three expanding 60-day validation folds, and alpha grid of 0.1, 1, 10, and 100.
Each version selects alpha using development validation. Fold-level results and
scores on the existing final test are reported as exploratory comparisons.

## Uncertainty in the improvement

A paired circular block bootstrap resamples the baseline and Ridge daily absolute
errors using the same dates for both models. The primary block length is seven
days, with three- and fourteen-day blocks as sensitivity checks. Each length uses
10,000 resamples and random seed 20261106 plus the block length.

The analysis reports percentile 95% intervals for the absolute reduction in MAE
and the percentage reduction, calculated as 100 × (1 − Ridge MAE / baseline MAE)
within each resample. Blocks preserve some local dependence between errors, but
the short and seasonally changing test period limits the approximation.

These intervals describe the fitted models over this period. They exclude
training and model-selection uncertainty and are not intervals for future daily
rental counts.

## Error patterns and prior volatility

The error audit groups the original Ridge errors by month, weekend status, and
recent volatility. Volatility is the preceding seven-day sample standard deviation
divided by the preceding seven-day mean. The flag marks values above the
75th percentile of development volatility.

For development-validation diagnostics, each fold’s threshold uses that fold’s
training rows only. No threshold is selected to improve the final-test result.
Because these folds also supported model selection, the diagnostic is descriptive
rather than an independent validation of the warning rule.

## Disruption context

Contemporaneous reporting and weather records provide context for Sandy and
late-December forecast errors. These sources do not become model inputs, and
all dates remain in the reported metrics. The case studies support interpretation
without assigning a causal effect to any single event. The presentation brings
these findings together with the original results and their limitations.
