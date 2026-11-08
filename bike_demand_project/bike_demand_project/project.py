"""Reproducible next-day rental forecasting. See EXPERIMENT_PLAN.md."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
import zipfile

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
URL = 'https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip'
CALENDAR = ['weekday', 'holiday', 'workingday', 'annual_sin', 'annual_cos', 'trend']
HISTORY = ['lag_1', 'lag_7', 'lag_14', 'mean_7', 'mean_28', 'std_7']
FEATURES = CALENDAR + HISTORY
CUTOFF = pd.Timestamp('2012-10-01')
plt.rcParams.update({'figure.dpi': 130, 'axes.spines.top': False,
                     'axes.spines.right': False, 'font.size': 10})


def load_data():
    path = ROOT / 'data/raw/day.csv'
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=30) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        for name in ['day.csv', 'Readme.txt']:
            (path.parent / name).write_bytes(archive.read(name))
    raw = pd.read_csv(path, parse_dates=['dteday']).sort_values('dteday').reset_index(drop=True)
    assert len(raw) == 731
    assert raw.isna().sum().sum() == 0
    assert raw.dteday.is_unique
    assert raw.dteday.diff().dropna().eq(pd.Timedelta(days=1)).all()
    assert raw.cnt.ge(0).all()
    assert raw.cnt.eq(raw.casual + raw.registered).all()
    audit = dict(rows=len(raw), columns=len(raw.columns), missing_cells=0,
                 duplicate_dates=0, start=str(raw.dteday.min().date()),
                 end=str(raw.dteday.max().date()), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 source=URL, retrieved='2026-11-06', daily_continuity=True,
                 total_equals_casual_plus_registered=True)
    (OUT / 'data_audit.json').write_text(json.dumps(audit, indent=2))
    return raw, audit


def make_features(raw):
    """Every target-derived input is shifted into the past BEFORE rolling."""
    d = raw[['dteday', 'cnt', 'holiday', 'workingday']].copy()
    d['weekday'] = d.dteday.dt.dayofweek  # Monday=0, unlike source's Sunday=0
    angle = 2 * np.pi * (d.dteday.dt.dayofyear - 1) / 365.25
    d['annual_sin'], d['annual_cos'] = np.sin(angle), np.cos(angle)
    d['trend'] = (d.dteday - pd.Timestamp('2011-01-01')).dt.days
    for lag in [1, 7, 14]:
        d[f'lag_{lag}'] = d.cnt.shift(lag)
    past = d.cnt.shift(1)
    d['mean_7'] = past.rolling(7).mean()
    d['mean_28'] = past.rolling(28).mean()
    d['std_7'] = past.rolling(7).std()
    return d.dropna(subset=FEATURES).reset_index(drop=True)


def check_features(raw, data):
    assert len(data) == len(raw) - 28
    assert data.dteday.min() == pd.Timestamp('2011-01-29')
    assert not {'cnt', 'casual', 'registered', 'temp', 'atemp', 'hum', 'windspeed', 'weathersit', 'instant'} & set(FEATURES)
    for i in [28, 365, 639, 730]:
        day = raw.loc[i, 'dteday']
        row = data.loc[data.dteday.eq(day)].iloc[0]
        assert row.lag_1 == raw.loc[i-1, 'cnt']
        assert row.lag_7 == raw.loc[i-7, 'cnt']
        assert np.isclose(row.mean_7, raw.loc[i-7:i-1, 'cnt'].mean())
        changed = raw.copy()
        changed.loc[i:, 'cnt'] = 1000000  # today's and future outcomes must not affect today's inputs
        other = make_features(changed).set_index('dteday').loc[day, FEATURES]
        np.testing.assert_allclose(row[FEATURES].to_numpy(dtype=float), other.to_numpy(dtype=float))
        prefix = make_features(raw.iloc[:i+1]).iloc[-1]
        np.testing.assert_allclose(row[FEATURES].to_numpy(dtype=float), prefix[FEATURES].to_numpy(dtype=float))
    return 'PASS: dates, counts, lag identities, prefix equivalence, and future-outcome perturbation checks.'


def pipeline(kind, parameter, features):
    numeric = [f for f in features if f != 'weekday']
    prep = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('weekday', OneHotEncoder(categories=[list(range(7))], handle_unknown='ignore', sparse_output=False), ['weekday'])
    ])
    estimator = (Ridge(alpha=parameter) if kind == 'ridge' else
                 GradientBoostingRegressor(n_estimators=parameter, learning_rate=0.05,
                                           max_depth=2, min_samples_leaf=10, random_state=42))
    return make_pipeline(prep, estimator)


def scores(y, prediction):
    return {'MAE': float(mean_absolute_error(y, prediction)),
            'RMSE': float(np.sqrt(mean_squared_error(y, prediction)))}


def develop(data):
    """This function receives development rows ONLY, so it cannot access test targets."""
    assert data.dteday.max() < CUTOFF
    splits = list(TimeSeriesSplit(n_splits=3, test_size=60).split(data))
    records, fold_info = [], []
    specifications = [('Same weekday last week', 'baseline', [0], FEATURES),
                      ('Ridge', 'ridge', [0.1, 1, 10, 100], FEATURES),
                      ('Gradient boosting', 'boost', [100, 250], FEATURES),
                      ('Calendar-only Ridge', 'ridge', [0.1, 1, 10, 100], CALENDAR)]
    for fold, (tr, va) in enumerate(splits, 1):
        train, valid = data.iloc[tr], data.iloc[va]
        assert train.dteday.max() < valid.dteday.min()
        fold_info.append(dict(fold=fold, train_start=str(train.dteday.min().date()),
                              train_end=str(train.dteday.max().date()), train_n=len(train),
                              validation_start=str(valid.dteday.min().date()),
                              validation_end=str(valid.dteday.max().date()), validation_n=len(valid)))
        for name, kind, parameters, features in specifications:
            for parameter in parameters:
                if kind == 'baseline':
                    pred = valid.lag_7.to_numpy()
                else:
                    model = pipeline(kind, parameter, features)
                    model.fit(train[features], train.cnt)
                    pred = np.maximum(0, model.predict(valid[features]))
                records.append(dict(model=name, parameter=parameter, fold=fold, **scores(valid.cnt, pred)))
    cv = pd.DataFrame(records)
    summary = cv.groupby(['model', 'parameter'], as_index=False).agg(MAE=('MAE', 'mean'), RMSE=('RMSE', 'mean'))
    chosen = summary.loc[summary.groupby('model').MAE.idxmin()].sort_values('MAE').reset_index(drop=True)
    winner = chosen.loc[chosen.model.ne('Calendar-only Ridge')].iloc[0]['model']
    models = {}
    for name, kind, _, features in specifications:
        if kind != 'baseline':
            parameter = float(chosen.loc[chosen.model.eq(name), 'parameter'].iloc[0])
            if kind == 'boost':
                parameter = int(parameter)
            fitted = pipeline(kind, parameter, features).fit(data[features], data.cnt)
            models[name] = {'pipeline': fitted, 'features': features}
    cv.to_csv(OUT / 'validation_all_candidates.csv', index=False)
    chosen.to_csv(OUT / 'validation_selected.csv', index=False)
    pd.DataFrame(fold_info).to_csv(OUT / 'validation_folds.csv', index=False)
    frozen = {'winner_chosen_before_test': winner,
              'selected_parameters': chosen[['model', 'parameter']].to_dict(orient='records'),
              'test_start': str(CUTOFF.date()), 'seed': 42}
    (OUT / 'frozen_selection.json').write_text(json.dumps(frozen, indent=2))
    joblib.dump(models, OUT / 'fitted_models.joblib')
    return models, chosen, winner, pd.DataFrame(fold_info)


def evaluate(test, models, winner):
    assert test.dteday.min() == CUTOFF
    predictions = test[['dteday', 'cnt', 'weekday']].copy()
    predictions['Same weekday last week'] = test.lag_7
    for name, bundle in models.items():
        predictions[name] = np.maximum(0, bundle['pipeline'].predict(test[bundle['features']]))
    names = ['Same weekday last week'] + list(models)
    metrics = pd.DataFrame([dict(model=name, **scores(test.cnt, predictions[name])) for name in names])
    baseline = float(metrics.loc[metrics.model.eq(names[0]), 'MAE'].iloc[0])
    metrics['MAE_improvement_pct'] = 100 * (1 - metrics.MAE / baseline)
    metrics['selected_before_test'] = metrics.model.eq(winner)
    metrics.to_csv(OUT / 'test_metrics.csv', index=False)
    predictions.to_csv(OUT / 'test_predictions.csv', index=False)
    failures = predictions[['dteday', 'cnt', winner]].copy()
    failures['error_prediction_minus_actual'] = failures[winner] - failures.cnt
    failures['absolute_error'] = failures.error_prediction_minus_actual.abs()
    failures.sort_values('absolute_error', ascending=False).head(10).to_csv(OUT / 'largest_errors.csv', index=False)
    grouped = []
    for label, mask in [('Weekdays', predictions.weekday < 5), ('Weekends', predictions.weekday >= 5)]:
        for name in [names[0], winner]:
            grouped.append(dict(group=label, model=name, days=int(mask.sum()), **scores(predictions.loc[mask, 'cnt'], predictions.loc[mask, name])))
    pd.DataFrame(grouped).to_csv(OUT / 'weekday_weekend_errors.csv', index=False)
    return metrics, predictions, failures.sort_values('absolute_error', ascending=False)


def plot_development(raw):
    d = raw[raw.dteday < CUTOFF]
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), layout='constrained')
    axes[0].plot(d.dteday, d.cnt, color='#c0ccd6', lw=0.8, label='Daily rentals')
    axes[0].plot(d.dteday, d.cnt.rolling(28).mean(), color='#147d92', lw=2, label='28-day mean (descriptive)')
    axes[0].set(title='Development data: demand changes over time', ylabel='Rentals per day')
    axes[0].legend(frameon=False)
    means = d.groupby(d.dteday.dt.dayofweek).cnt.mean()
    axes[1].bar(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], means, color='#147d92')
    axes[1].set(title='Average demand by weekday — development data only', ylabel='Rentals per day')
    fig.savefig(OUT / 'development_patterns.png', bbox_inches='tight')
    return fig


def plot_results(metrics, predictions, winner):
    fig, ax = plt.subplots(figsize=(9, 4.2), layout='constrained')
    order = metrics.sort_values('MAE', ascending=False)
    bars = ax.barh(order.model, order.MAE, color=['#147d92' if n == winner else '#a9bac8' for n in order.model])
    ax.bar_label(bars, fmt='%.0f', padding=5)
    ax.set(xlabel='Mean absolute error (rentals/day) — lower is better', title='Final test: October–December 2012', xlim=(0, metrics.MAE.max()*1.18))
    fig.savefig(OUT / 'model_comparison.png', bbox_inches='tight')
    fig2, axes = plt.subplots(2, 1, figsize=(11, 7), layout='constrained')
    axes[0].plot(predictions.dteday, predictions.cnt, color='#243746', label='Actual', lw=1.6)
    axes[0].plot(predictions.dteday, predictions[winner], color='#147d92', label=f'{winner} (selected on validation)', lw=1.5)
    axes[0].plot(predictions.dteday, predictions['Same weekday last week'], color='#d5a24b', alpha=.55, label='Last-week baseline', lw=.9)
    axes[0].set(title='Rolling one-day-ahead forecasts on unseen dates', ylabel='Rentals per day')
    axes[0].legend(frameon=False, fontsize=9)
    error = predictions[winner] - predictions.cnt
    axes[1].bar(predictions.dteday, error, color=np.where(error >= 0, '#147d92', '#d5a24b'))
    axes[1].axhline(0, color='#243746', lw=.7)
    axes[1].set(title='Where the selected model misses', ylabel='Predicted − actual rentals', xlabel='Forecast date (2012)')
    fig2.savefig(OUT / 'forecasts_and_errors.png', bbox_inches='tight')
    return fig, fig2
