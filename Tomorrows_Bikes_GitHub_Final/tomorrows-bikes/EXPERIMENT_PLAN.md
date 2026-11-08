# Original experiment design

This document records the choices fixed before fitting the original models or
inspecting their scores. The aim is to forecast total rentals on day t just after
day t−1 ends, assuming the completed day’s total is available immediately.

## Data and predictors

The target is `cnt` in the UCI Bike Sharing daily dataset. Calendar predictors
include weekday, holiday and working-day indicators, annual sine and cosine terms,
and elapsed days. Rental-history predictors include lags of 1, 7, and 14 days,
means over the preceding 7 and 28 days, and the preceding 7-day standard deviation.
All rolling statistics use counts shifted back by one day.

Target-day weather, `casual`, `registered`, and the record identifier are excluded.
There are no external data joins. The first 28 rows lack a complete history window
and are omitted without imputation. All later observations remain, including
unusual days.

## Validation and final test

Development data run through September 30, 2012. Three expanding validation folds
each contain 60 days, with every training date earlier than its validation window.
The final test covers October 1 through December 31, 2012 and does not influence
feature choices, model selection, or hyperparameters in the original experiment.

The primary metric is mean absolute error (MAE), measured in rentals per day.
Root mean squared error (RMSE) provides a secondary measure that gives more weight
to large misses. The main model is selected by average validation MAE.

## Model candidates

| Method | Settings |
|---|---|
| Last-week baseline | Rental count from day t−7 |
| Ridge regression | Standardized numeric features and one-hot weekdays; alpha 0.1, 1, 10, or 100 |
| Gradient boosting | Squared-error loss, learning rate 0.05, depth 2, minimum leaf size 10; 100 or 250 trees; seed 42 |
| Calendar-only Ridge | Explanatory comparison with the same alpha grid, excluded from main model selection |

Preprocessing is fitted separately within each training fold. After selection,
learned models are refitted on all development data and evaluated on the final
test. Predictions are clipped at zero because rental counts cannot be negative.

Models stay fixed within each validation or test window. Each daily prediction
uses actual totals from completed days, making this a sequence of one-day-ahead
forecasts rather than a single forecast for the entire window.

## Checks and interpretation

Data checks cover missing values, duplicate or interrupted dates, nonnegative
counts, and agreement between total rentals and their components. Feature checks
verify lag identities and confirm that changing current or future outcomes cannot
change the current day’s predictors.

The analysis reports large misses and weekday/weekend errors without removing
those observations. Its scope is limited to two years from one historical system.
System totals do not reveal station shortages, and observed rentals do not measure
unmet demand. The experiment does not estimate causal effects or operational savings.
