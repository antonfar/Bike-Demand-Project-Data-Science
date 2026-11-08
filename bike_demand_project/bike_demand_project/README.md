# Tomorrow’s bikes

Can calendar information and past rental counts predict the next day's total
Capital Bikeshare rentals better than the same weekday last week?

## Start here

1. Open `bike\_demand\_report.html` in a browser for results and a beginner walkthrough.
2. Read `bike\_demand.ipynb` for the explained, executed analysis.
3. Read `EXPERIMENT\_PLAN.md` for the decisions fixed before fitting.
4. Read `project.py` for the feature engineering, model fitting, checks and plots.
5. Read `EXTENSION\_PLAN.md` and `extensions.py` for the exploratory additions.
6. Open `slides/Tomorrow\_s\_Bikes.pptx` for editable slides, or the PDF for viewing.

The data, code, trained models, predictions and evaluation outputs are included.
No API keys or GPU are needed. The HTML report works offline.

## Reproduce

Tested with Python 3.12. From this extracted folder:

```sh
python -m venv .venv
# Activate .venv using the command appropriate for your operating system.
python -m pip install -r requirements.txt
python run\_project.py
```

This executes every Python cell in the notebook and saves the notebook's real
outputs, plots, metrics, fitted models and HTML report. It is a runner for this
specific plain-Python notebook, not a general replacement for Jupyter. For an
interactive session, open the notebook in a Python notebook editor with these
dependencies and this project folder as its working directory.

The bundled data permit offline reruns. If `data/raw/day.csv` is absent, the
code fetches the UCI archive. All paths are relative to the project folder.
Only load the bundled joblib model file if you trust the project source;
rerunning the training code recreates it.

## Experiment

* 731 daily records; 28 initial days establish lagged inputs.
* 611 development dates: January 29, 2011–September 30, 2012.
* 92 final test dates: October 1–December 31, 2012.
* Three expanding validation folds, each with 60 later days.
* Main methods: same-weekday-last-week baseline, Ridge regression and gradient boosting.
* Explanatory comparison: Ridge with calendar features only.
* Primary metric: mean absolute error (MAE), in rentals/day.
* Select the main method using validation, not final test performance.
* Models remain fixed throughout each evaluation window. Yesterday's actual
count is available before today's prediction. This is rolling daily forecasting,
not a three-month forecast made all at once.

No target-day weather or component counts enter the inputs. Scaling is fitted
within each training fold. Automated assertions check date continuity, target
consistency and that changes to current/future outcomes cannot alter current
features. The untouched test is evaluated after selection is saved.

## Outputs

* `results/summary.json`: headline results.
* `results/test\_metrics.csv`: final comparison, including the preselected model flag.
* `results/test\_predictions.csv`: every test date, actual and prediction.
* `results/validation\_all\_candidates.csv`: all validation scores.
* `results/validation\_selected.csv`: chosen setting per family.
* `results/frozen\_selection.json`: model selection saved before test evaluation.
* `results/largest\_errors.csv`, `results/weekday\_weekend\_errors.csv`: error analysis.
* `results/data\_audit.json`: checks, source and SHA-256 fingerprint.
* `results/fitted\_models.joblib`: all three fitted learned pipelines.

## Exploratory extensions

These were designed after seeing the original test, so they do not constitute
new confirmatory evidence. Original model selection and predictions are preserved.

* Feature comparison: calendar-only, history-only and combined Ridge.
* Paired circular block bootstrap: 10,000 resamples and 3/7/14-day sensitivity.
* Prior-volatility flag: thresholds use only earlier training dates.
* Documented disruption case studies: see `EVENT\_CONTEXT.md`.
* All extension tables, charts, draws and checks: `results/extensions/`.

The notebook runs these additions after the original pipeline. The PowerPoint
contains editable native charts and tables, with methods and sources in notes.
The PDF is a visual export.

## Limits

Two historical years from one system cannot establish present-day performance.
The final test covers only autumn/early winter. Rental counts are observed use,
not unmet demand. System totals do not identify station shortages. No causal
claims, financial benefits or operational improvements are established.
The exploratory block-bootstrap intervals condition on the fitted models and
this short historical test period; they omit training and selection uncertainty. The forecast assumes complete prior-day totals are immediately
available; an earlier forecast would need different features. No historical
weather forecasts are available in this dataset.

Further model changes after inspecting these results must be labeled exploratory
or evaluated on a new untouched period. The existing test is no longer unseen.

## Data attribution

Fanaee-T, H. (2013). Bike Sharing \[Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C5W894

Dataset page: https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset

UCI lists the data under CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/

Associated paper: Fanaee-T, H. and Gama, J. (2013). Event labeling combining
ensemble detectors and background knowledge.
https://doi.org/10.1007/s13748-013-0040-3

The source CSV and original README are preserved unchanged. Feature tables
and model outputs are derived from those data. Retrieved November 6, 2026.

