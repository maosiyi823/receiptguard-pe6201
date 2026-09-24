"""Build an offline viewer of recorded outputs, with no credentials or API calls."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run=ROOT/'results/final_20260924T122051343232Z'
inputs=json.loads((ROOT/'data/frozen_v1/inputs.json').read_text())
labels={c['case_id']:c for c in json.loads((ROOT/'data/frozen_v1/labels.json').read_text())}
rows={c['case_id']:c for c in map(json.loads,(run/'cases.jsonl').read_text().splitlines())}
cases=[]
for c in inputs:
 r=rows[c['case_id']]
 cases.append({**c,'label':labels[c['case_id']],'result':{k:r[k] for k in ('regex','ai')}})
data={'run':run.name,'summary':json.loads((run/'summary.json').read_text()),'cases':cases}
encoded=json.dumps(data,ensure_ascii=True).replace('<','\\u003c')
(ROOT/'demo/index.html').write_text((ROOT/'demo/template.html').read_text().replace('__DATA__',encoded))
print('Built offline recorded-results viewer with 50 cases; no request credentials included.')
