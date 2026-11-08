"""Execute this project's notebook in order and save its real outputs.

No Jupyter installation is needed for this notebook (plain Python cells only).
To work interactively instead, open bike_demand.ipynb in Jupyter or VS Code.
"""
from pathlib import Path
import base64
import contextlib
import html
import io
import json
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
path = ROOT / 'bike_demand.ipynb'
notebook = json.loads(path.read_text())
namespace = {'__name__': '__main__'}
execution = 0
for cell in notebook['cells']:
    if cell['cell_type'] != 'code':
        continue
    execution += 1
    outputs = []
    stream = io.StringIO()

    def flush_text():
        text = stream.getvalue()
        if text:
            outputs.append({'output_type': 'stream', 'name': 'stdout', 'text': text})
            stream.seek(0)
            stream.truncate(0)

    def capture_show(*args, **kwargs):
        flush_text()
        for number in plt.get_fignums():
            figure = plt.figure(number)
            buffer = io.BytesIO()
            figure.savefig(buffer, format='png', bbox_inches='tight')
            outputs.append({'output_type': 'display_data', 'metadata': {},
                            'data': {'image/png': base64.b64encode(buffer.getvalue()).decode(),
                                     'text/plain': 'Matplotlib figure'}})
        plt.close('all')

    plt.show = capture_show
    with contextlib.redirect_stdout(stream):
        exec(compile(cell['source'], f'notebook-cell-{execution}', 'exec'), namespace)
    flush_text()
    cell['execution_count'] = execution
    cell['outputs'] = outputs
    print(f'Executed cell {execution}')
path.write_text(json.dumps(notebook, indent=1))

# A self-contained, read-only report: figures and notebook outputs embedded.
metrics = namespace['metrics']
winner = namespace['winner']
selected = metrics.loc[metrics.model.eq(winner)].iloc[0]
baseline = metrics.loc[metrics.model.eq('Same weekday last week')].iloc[0]
summary = {
    'selected_model': winner, 'test_days': len(namespace['test']),
    'test_MAE': float(selected.MAE), 'baseline_MAE': float(baseline.MAE),
    'MAE_improvement_pct': float(selected.MAE_improvement_pct),
    'development_days': len(namespace['development']),
}
(ROOT / 'results/summary.json').write_text(json.dumps(summary, indent=2))

parts = ['''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tomorrow’s bikes — data and models</title><style>
body{font:17px/1.65 system-ui,sans-serif;color:#243746;background:#f4f7f9;margin:0}
main{max-width:1060px;margin:auto;padding:48px 32px}h1{font-size:44px;line-height:1.12}
h2{margin-top:36px;color:#126b7d}.kicker{color:#126b7d;letter-spacing:.12em;font-size:13px;font-weight:700}
.cards{display:flex;gap:16px;flex-wrap:wrap}.card{background:#fff;padding:22px;border-radius:12px;flex:1;min-width:180px}
.big{display:block;font-size:34px;font-weight:700;color:#126b7d}section{background:white;border-radius:12px;padding:24px;margin:24px 0}
img{width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,monospace;background:#eef3f6;padding:16px;border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:12px;border-bottom:1px solid #dce5eb}
details{margin:16px 0}summary{cursor:pointer;font-weight:600}a{color:#126b7d}.tablewrap{overflow-x:auto}
</style><main><div class="kicker">CAPITAL BIKESHARE · HISTORICAL FORECASTING STUDY</div>
<h1>Tomorrow’s bikes</h1><p>Can past rentals and calendar information improve a next-day forecast?</p>''']
parts.append(f'<div class="cards"><div class="card">Selected using validation<span class="big">{html.escape(winner)}</span></div><div class="card">Test error, rentals/day<span class="big">{selected.MAE:,.0f}</span></div><div class="card">Less MAE than last week<span class="big">{selected.MAE_improvement_pct:.1f}%</span></div></div>')
parts.append('<section><h2>What we measured</h2><p>731 days of real rental data; 28 days used to establish history; 611 development days and 92 final test days. Every prediction uses information available just after the preceding day closes. The final test covers October–December 2012.</p><p>The selected model was chosen on three earlier validation windows. All model settings were locked before inspecting the final test. MAE is the average absolute miss in rental counts; it is not a percentage accuracy score.</p>')
parts.append('<div class="tablewrap">'+metrics.round(2).to_html(index=False,border=0)+'</div>')
parts.append('<p>The calendar-only model is an explanatory comparison. Reported performance is limited to this historical period; it does not demonstrate current-system performance or operational savings.</p></section>')
for filename in ['model_comparison.png', 'forecasts_and_errors.png']:
    image = base64.b64encode((ROOT / 'results' / filename).read_bytes()).decode()
    parts.append(f'<section><img alt="{filename.replace("_", " ")}" src="data:image/png;base64,{image}"></section>')
parts.append('<section><h2>How to learn from this project</h2><p>Read the walkthrough below, then open the notebook to change code and rerun it. Keep the final test results fixed when reporting this experiment; later changes are exploratory unless tested on new data.</p></section>')
for cell in notebook['cells']:
    if cell['cell_type'] == 'markdown':
        # Small renderer for this notebook's headings, links, emphasis and code.
        source = cell['source']
        title, _, body = source.partition('\n')
        parts.append('<section><h2>'+html.escape(title.lstrip('# '))+'</h2>')
        for paragraph in body.strip().split('\n\n'):
            rendered = html.escape(paragraph)
            rendered = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', rendered)
            rendered = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', rendered)
            rendered = re.sub(r'`([^`]+)`', r'<code>\1</code>', rendered)
            if rendered.startswith('## '):
                parts.append('<h2>'+rendered[3:]+'</h2>')
            else:
                parts.append('<p>'+rendered.replace('\n', '<br>')+'</p>')
        parts.append('</section>')
    else:
        parts.append('<details><summary>Code and recorded outputs</summary><pre>'+html.escape(cell['source'])+'</pre>')
        for output in cell['outputs']:
            if output['output_type'] == 'stream':
                parts.append('<pre>'+html.escape(output['text'])+'</pre>')
            elif 'image/png' in output.get('data', {}):
                parts.append('<img alt="Analysis figure" src="data:image/png;base64,'+output['data']['image/png']+'">')
        parts.append('</details>')
parts.append('</main></html>')
(ROOT / 'bike_demand_report.html').write_text('\n'.join(parts))
print(json.dumps(summary, indent=2))
