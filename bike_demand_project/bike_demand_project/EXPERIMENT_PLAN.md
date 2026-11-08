# Frozen experiment plan

Written before model fitting or inspecting model scores.

- Question: forecast the total rentals on day t, immediately after day t-1 closes.
- Assumption: the complete previous day's total is immediately available. An earlier evening forecast would require different inputs.
- Target: `cnt` from UCI Bike Sharing's `day.csv`.
- Main inputs: known calendar (weekday, holiday, working day, annual sine/cosine, elapsed days), rental lags 1/7/14 days, and strictly past rolling mean 7/28 days and standard deviation 7 days.
- Exclude target-day weather, `casual`, `registered`, and record ID. No external data joins.
- First 28 rows cannot supply full history; drop these, do not impute them.
- Development data: all eligible dates before 2012-10-01.
- Final test: 2012-10-01 through 2012-12-31. Never use it to select features, models or hyperparameters.
- Validation: three expanding-window folds, each with 60 validation days; all training dates precede validation dates.
- Primary metric: MAE in rentals/day. Secondary metric: RMSE, which weights large misses more heavily.
- Baseline: same weekday last week, i.e. count from t-7.
- Ridge: standardized numeric inputs plus one-hot weekdays; alpha in [0.1, 1, 10, 100].
- Gradient boosting: squared-error loss, learning rate 0.05, max depth 2, min leaf 10; n_estimators in [100, 250]. Seed 42.
- Additional explanatory experiment: calendar-only Ridge, with its alpha selected on the same validation folds. Not a candidate for the main winner.
- Main model chosen by average validation MAE across baseline, Ridge and gradient boosting. Refit learned models on all development data, then evaluate all locked choices on test once.
- All learned preprocessing is fitted separately within each training fold. Predictions clipped to zero because rental counts cannot be negative.
- During validation and test, models stay fixed within each fold, but each next daily prediction receives actual rental totals from completed prior days. This is rolling one-day-ahead evaluation, NOT a 60/92-day forecast made in one shot.
- Report failures and weekday/weekend errors; do not remove unusual days.
- Checks: unique uninterrupted daily index, nonnegative counts, component-count identity, chronological folds, lag identities, and unchanged features for day t when t and future targets change.
- Limitations: two years from one historical system; observed rentals are not unmet demand; system totals cannot predict station shortages; no forecast weather, causal claims or demonstrated operational savings.
