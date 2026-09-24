"""Build an English comparison from saved real runs. Makes no API calls."""
import json
from pathlib import Path
from receiptguard import FIELDS, fields_match

ROOT=Path(__file__).parent

def field_rates(cases, rows, method, raw):
    result={}
    for field in FIELDS:
        count=0
        for c,r in zip(cases,rows):
            pred=r[method]
            values=pred.get('raw_fields',pred['fields']) if raw else pred['fields']
            count+=fields_match({field:values.get(field)}, {field:c['ground_truth_fields'].get(field)})
        result[field]=f'{count}/{len(rows)}'
    return result

def main():
    cases=json.loads((ROOT/'data/dev.json').read_text())
    indexed={c['case_id']:c for c in cases}
    lines=['# Saved development run comparison','','Generated from archived outputs; no new requests. Development evidence only.','', '| Run | Prompt | Cases | AI raw date / currency / total | AI validated date / currency / total | Correct automated handling |', '|---|---|---:|---|---|---|']
    runs=[]
    for folder in sorted((ROOT/'results').glob('development_*')):
        if not folder.is_dir() or not (folder/'summary.json').exists():continue
        summary=json.loads((folder/'summary.json').read_text())
        rows=[json.loads(s) for s in (folder/'cases.jsonl').read_text().splitlines()]
        if not rows:continue
        selected=[indexed[r['case_id']] for r in rows]
        prompt='v2' if 'prompts/extract_v2.txt' in summary['hashes'] else 'v1'
        raw=field_rates(selected,rows,'ai',True);validated=field_rates(selected,rows,'ai',False)
        good=summary['summary']['ai']['correct_automated_count']
        lines.append(f"| {folder.name} | {prompt} | {len(rows)}/14 | {' / '.join(raw.values())} | {' / '.join(validated.values())} | {good}/{len(rows)} |")
        runs.append(prompt)
    lines+=['','Raw fields measure extractor output. Validated fields measure output after deterministic checks. Old runs without raw_fields use their original fields; those initial logs predate value-clearing validation.','', 'A new v2 live run is available.' if 'v2' in runs else '**Pending: no live v2 run has been saved. The offline replay is not a new model experiment.**']
    out=ROOT/'docs/SAVED_RUN_COMPARISON.md';out.write_text('\n'.join(lines)+'\n')
    print(out)

if __name__=='__main__':main()
