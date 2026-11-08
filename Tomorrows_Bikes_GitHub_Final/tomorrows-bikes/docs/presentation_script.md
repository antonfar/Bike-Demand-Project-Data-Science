# Presentation transcript

A five-minute overview of the research question, evaluation, findings, and limitations.

## Slide 1 — Tomorrow's bikes

My project looks at whether recent bike rentals can help predict the next day's activity. Using Capital Bikeshare data, I found that they can, although the forecasts struggle when normal patterns suddenly break down.

## Slide 2 — The forecasting question

The practical idea is to help operators anticipate busy or quiet days across the system. For that to work, the forecast uses information available just after the previous day ends. There's also an important distinction here: we're predicting recorded rentals, so a service closure can reduce the count even when people still want bikes.

## Slide 3 — Data and available inputs

To study this, I used seven hundred thirty-one daily records from twenty eleven and twenty twelve. The inputs combine calendar information with earlier rental counts and rolling averages, using the first twenty-eight days to establish that history. I excluded the target day's observed weather and rental components because those wouldn't be available when making the prediction.

## Slide 4 — Testing in chronological order

That same concern about available information shaped the testing approach. I used three earlier validation windows to choose the model, then evaluated it on ninety-two days from October through December twenty twelve. Within each window, the model stayed fixed, but each completed day's count became available for the next forecast. This keeps the evaluation close to how daily forecasting would work.

## Slide 5 — Models and error measurement

For the comparison, I started with a simple baseline: predict the same count as the same weekday last week. I then tested Ridge regression, which combines inputs with a penalty to keep coefficients stable, and gradient boosting, which combines small decision trees. I compared them using mean absolute error, or M A E, which measures the average daily miss in rentals.

## Slide 6 — The original result

Ridge performed best during validation, and that choice carried through to the final test. Its average error was nine hundred thirty-nine rentals per day, compared with fourteen hundred fifty-eight for the baseline: a thirty-five point six percent reduction. The more flexible boosting model didn't improve on Ridge, and all test days, including the difficult ones, remain in these scores.

## Slide 7 — Which inputs help

With that improvement established, I wanted to understand which inputs were helping. Calendar information alone performed worse, while history-only and combined Ridge performed similarly, suggesting recent counts carry much of the signal. Because I added this comparison after seeing the test results, I treat it as exploratory and keep the original model selection.

## Slide 8 — Uncertainty around the improvement

I also examined how uncertain that improvement might be by resampling seven-day blocks ten thousand times, keeping both models' errors paired. The approximate ninety-five percent interval for error reduction was twenty-one to fifty percent, so the advantage remained positive. Still, this estimate applies to the fitted models and this short historical period; it leaves out uncertainty from training and model selection.

## Slide 9 — Where the forecasts fail

That average advantage doesn't tell the whole story, though. Looking at individual days, the model follows broad patterns but misses sudden drops. On October twenty-ninth, for example, it predicted roughly fifty-nine hundred rentals, while the dataset records just twenty-two.

## Slide 10 — Context for the largest misses

Looking into that date helps explain why service availability matters. Reports describe an approximately thirty-six-hour Bikeshare shutdown during Hurricane Sandy, while weather reports provide context for December misses. These sources don't tell us exactly how much each event caused, but they show why interpreting rental counts requires knowing what was happening to the service.

## Slide 11 — An imperfect warning flag

That led to an exploratory warning flag based on recent variability. Flagged days had higher average errors, but it missed the first Sandy shutdown day, showing how a signal based on past counts can react too late.

## Slide 12 — Conclusion and next experiment

Taken together, the results suggest recent rental history is useful, but sudden disruptions remain a blind spot. I'd next test archived service notices and weather forecasts on new dates, since these historical results alone don't establish how the model would perform today.

## Slide 13 — Reproducibility appendix

I've included the settings and sensitivity checks here for reference.

## Slide 14 — Sources and closing

And these are the sources behind the analysis. Thank you.
