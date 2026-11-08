"""Exploratory diagnostics. Never rewrites original model/prediction outputs."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import project as p

OUT = p.ROOT / 'results/extensions'
OUT.mkdir(parents=True, exist_ok=True)


def ridge(features, alpha):
    if 'weekday' in features:
        return p.pipeline('ridge', alpha, features)
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def run():
    protected = ['test_predictions.csv', 'test_metrics.csv', 'frozen_selection.json', 'fitted_models.joblib']
    before = {n: hashlib.sha256((p.OUT/n).read_bytes()).hexdigest() for n in protected}
    raw = pd.read_csv(p.ROOT/'data/raw/day.csv', parse_dates=['dteday'])
    data = p.make_features(raw)
    dev = data[data.dteday < p.CUTOFF].copy()
    test = data[data.dteday >= p.CUTOFF].copy()
    original = pd.read_csv(p.OUT/'test_predictions.csv', parse_dates=['dteday'])
    splits = list(TimeSeriesSplit(n_splits=3, test_size=60).split(dev))
    feature_sets = {'Calendar only': p.CALENDAR, 'History only': p.HISTORY, 'Calendar + history': p.FEATURES}
    cv, fitted, ablations, oof = [], {}, [], []
    for name, features in feature_sets.items():
        for alpha in [.1, 1, 10, 100]:
            for fold, (tr, va) in enumerate(splits, 1):
                model = ridge(features, alpha).fit(dev.iloc[tr][features], dev.iloc[tr].cnt)
                pred = np.maximum(0, model.predict(dev.iloc[va][features]))
                cv.append(dict(features=name, alpha=alpha, fold=fold, **p.scores(dev.iloc[va].cnt, pred)))
        scores = pd.DataFrame([x for x in cv if x['features'] == name])
        average = scores.groupby('alpha').MAE.mean()
        best = float(average.idxmin())
        model = ridge(features, best).fit(dev[features], dev.cnt)
        fitted[name] = model
        pred = np.maximum(0, model.predict(test[features]))
        if name == 'Calendar + history':
            np.testing.assert_allclose(pred, original.Ridge, rtol=1e-10)
        if name == 'Calendar only':
            np.testing.assert_allclose(pred, original['Calendar-only Ridge'], rtol=1e-10)
        ablations.append(dict(features=name, alpha=best, validation_MAE=float(average.min()),
                              test_MAE=p.scores(test.cnt, pred)['MAE']))
        if name == 'History only':
            pd.DataFrame({'dteday':test.dteday, 'cnt':test.cnt, 'prediction':pred}).to_csv(OUT/'history_only_predictions.csv',index=False)
        if name == 'Calendar + history':
            for fold, (tr, va) in enumerate(splits,1):
                train,valid=dev.iloc[tr],dev.iloc[va]
                mod=ridge(features,best).fit(train[features],train.cnt)
                pr=np.maximum(0,mod.predict(valid[features]))
                threshold=float((train.std_7/train.mean_7).quantile(.75))
                for (_,row),pred_i in zip(valid.iterrows(),pr):
                    oof.append(dict(dteday=row.dteday,fold=fold,actual=row.cnt,prediction=pred_i,
                                    absolute_error=abs(row.cnt-pred_i),volatility=row.std_7/row.mean_7,
                                    threshold=threshold,high_volatility=row.std_7/row.mean_7>threshold))
    cv=pd.DataFrame(cv); ablations=pd.DataFrame(ablations)
    cv.to_csv(OUT/'ablation_all_cv.csv',index=False)
    ablations.to_csv(OUT/'ablation_summary.csv',index=False)
    selected=cv.merge(ablations[['features','alpha']],on=['features','alpha'])
    selected.to_csv(OUT/'ablation_selected_folds.csv',index=False)

    base_error=np.abs(original['Same weekday last week'].to_numpy()-original.cnt.to_numpy())
    ridge_error=np.abs(original.Ridge.to_numpy()-original.cnt.to_numpy())
    point=100*(1-ridge_error.mean()/base_error.mean())
    n=len(original); summaries=[]; primary=None
    for length in [3,7,14]:
        rng=np.random.default_rng(20261106+length)
        starts=rng.integers(0,n,size=(10000,int(np.ceil(n/length))))
        indexes=((starts[:,:,None]+np.arange(length))%n).reshape(10000,-1)[:,:n]
        b=base_error[indexes].mean(axis=1); r=ridge_error[indexes].mean(axis=1)
        improvement=100*(1-r/b); difference=b-r
        summaries.append(dict(block_days=length,resamples=10000,point_improvement_pct=point,
                              improvement_low=float(np.quantile(improvement,.025)),improvement_high=float(np.quantile(improvement,.975)),
                              point_MAE_reduction=float(base_error.mean()-ridge_error.mean()),
                              reduction_low=float(np.quantile(difference,.025)),reduction_high=float(np.quantile(difference,.975))))
        if length==7:
            primary=improvement
            pd.DataFrame({'MAE_improvement_pct':improvement,'MAE_reduction':difference}).to_csv(OUT/'bootstrap_7day_draws.csv',index=False)
    bootstrap=pd.DataFrame(summaries)
    bootstrap.to_csv(OUT/'bootstrap_summary.csv',index=False)

    errors=original[['dteday','cnt','Ridge','Same weekday last week']].copy()
    errors['absolute_error']=ridge_error
    errors['baseline_absolute_error']=base_error
    errors['month']=errors.dteday.dt.strftime('%B')
    errors['weekend']=errors.dteday.dt.dayofweek>=5
    errors=errors.merge(test[['dteday','mean_7','std_7']],on='dteday',validate='one_to_one')
    threshold=float((dev.std_7/dev.mean_7).quantile(.75))
    errors['volatility']=errors.std_7/errors.mean_7
    errors['high_volatility']=errors.volatility>threshold
    errors.to_csv(OUT/'test_error_audit.csv',index=False)
    groups=[]
    for dimension in ['month','weekend','high_volatility']:
        for group, part in errors.groupby(dimension,sort=False):
            groups.append(dict(dimension=dimension,group=str(group),days=len(part),
                               Ridge_MAE=float(part.absolute_error.mean()),baseline_MAE=float(part.baseline_absolute_error.mean())))
    group_df=pd.DataFrame(groups);group_df.to_csv(OUT/'error_groups.csv',index=False)
    oof=pd.DataFrame(oof);oof.to_csv(OUT/'validation_volatility_audit.csv',index=False)
    risk=[]
    for period, frame in [('Development validation',oof),('Final test',errors)]:
        for flag,part in frame.groupby('high_volatility'):
            risk.append(dict(period=period,group='High prior volatility' if flag else 'Other days',days=len(part),MAE=float(part.absolute_error.mean())))
    risk=pd.DataFrame(risk);risk.to_csv(OUT/'volatility_summary.csv',index=False)

    # Charts for the notebook/report. The slide deck recreates these as editable charts.
    fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
    xs=np.arange(3)
    ax.bar(xs-.18,ablations.validation_MAE,width=.36,label='Validation',color='#9CB7C6')
    ax.bar(xs+.18,ablations.test_MAE,width=.36,label='Final test (exploratory)',color='#117D8D')
    ax.set(xticks=xs,xticklabels=ablations.features,ylabel='MAE (rentals/day)',title='Which information helps Ridge?')
    ax.legend(frameon=False);fig.savefig(OUT/'ablation.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
    ax.hist(primary,bins=35,color='#117D8D',alpha=.85)
    bounds=bootstrap[bootstrap.block_days.eq(7)].iloc[0]
    for x in [bounds.improvement_low,bounds.improvement_high]: ax.axvline(x,color='#B46A32',ls='--')
    ax.axvline(point,color='#243746',lw=2,label=f'Observed improvement: {point:.1f}%')
    ax.set(xlabel='Reduction in MAE versus last-week baseline (%)',ylabel='Resamples',title='Approximate uncertainty within the 92-day test period')
    ax.legend(frameon=False);fig.savefig(OUT/'bootstrap.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
    ax.plot(errors.dteday,errors.cnt,label='Recorded rentals',color='#243746')
    ax.plot(errors.dteday,errors.Ridge,label='Ridge forecast',color='#117D8D')
    for day,label,y in [('2012-10-29','Oct 29: Sandy shutdown',8500),('2012-12-24','Dec 24: rain / holiday period',7500),('2012-12-26','Dec 26: regional winter storm',6500)]:
        r=errors[errors.dteday.eq(pd.Timestamp(day))].iloc[0]
        ax.annotate(label,xy=(r.dteday,r.cnt),xytext=(r.dteday-pd.Timedelta(days=20),y),fontsize=8,
                    arrowprops={'arrowstyle':'-','color':'#B46A32'})
    ax.set(ylabel='Rentals/day',title='Observed rentals reflect service availability as well as demand',ylim=(0,9000))
    ax.legend(frameon=False,loc='upper left');fig.savefig(OUT/'failure_timeline.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
    for j,period in enumerate(['Development validation','Final test']):
        frame=risk[risk.period.eq(period)].set_index('group').loc[['Other days','High prior volatility']]
        bars=ax.bar(np.arange(2)+(j-.5)*.36,frame.MAE,width=.36,label=period,color=['#9CB7C6','#117D8D'][j])
        ax.bar_label(bars,labels=[f'{x:.0f}\nn={n}' for x,n in zip(frame.MAE,frame.days)],fontsize=9,padding=3)
    ax.set(xticks=[0,1],xticklabels=['Other days','High prior volatility'],ylabel='Ridge MAE (rentals/day)',title='Does recent volatility warn of larger errors?')
    ax.legend(frameon=False);ax.set_ylim(0,risk.MAE.max()*1.3)
    fig.savefig(OUT/'volatility.png',bbox_inches='tight');plt.close(fig)
    counts,edges=np.histogram(primary,bins=np.arange(-10,81,3))
    chart_data={
        'ablation':ablations.to_dict(orient='records'),
        'ablation_folds':selected.to_dict(orient='records'),
        'bootstrap':bootstrap.to_dict(orient='records'),
        'bootstrap_histogram':{'categories':[f'{a:.0f}' for a in (edges[:-1]+edges[1:])/2], 'counts':counts.tolist()},
        'risk':risk.to_dict(orient='records'), 'error_groups':groups,
        'volatility_threshold':threshold,
        'timeline':{'dates':errors.dteday.dt.strftime('%b %d').tolist(),'actual':errors.cnt.tolist(),'ridge':errors.Ridge.tolist()},
        'cases':errors.loc[errors.dteday.isin(pd.to_datetime(['2012-10-29','2012-10-30','2012-12-24','2012-12-26']))].assign(dteday=lambda x:x.dteday.dt.strftime('%Y-%m-%d')).to_dict(orient='records')
    }
    (OUT/'slide_data.json').write_text(json.dumps(chart_data,indent=2))
    after={n:hashlib.sha256((p.OUT/n).read_bytes()).hexdigest() for n in protected}
    assert before==after,'Original results changed!'
    checks={'original_files_unchanged':before,'original_Ridge_predictions_reproduced':True,
            'bootstrap_pairs_preserved':True,'random_seed_base':20261106,
            'volatility_threshold':threshold,'status':'exploratory'}
    (OUT/'extension_checks.json').write_text(json.dumps(checks,indent=2))
    print('FEATURE COMPARISON\n',ablations.round(2).to_string(index=False))
    print('BOOTSTRAP\n',bootstrap.round(2).to_string(index=False))
    print('VOLATILITY\n',risk.round(2).to_string(index=False))
    print('GROUPS\n',group_df.round(2).to_string(index=False))
    return chart_data

if __name__=='__main__': run()
