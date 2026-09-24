"""Run the frozen 50-case evaluation once; credentials are never saved."""
import getpass
import hashlib
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from ai_client import extract_ai, ConnectionProblem
from common_validation import validate_evidence
from receiptguard import extract, assess, FIELDS, fields_match, evaluate
from run_development import score
ROOT=Path(__file__).parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root=ROOT):
    manifest=json.loads((root/'data/frozen_v1/manifest.json').read_text())
    for name,expected in manifest['hashes'].items():
        if sha(root/name)!=expected:raise ValueError('Frozen file changed: '+name)
    return manifest


def metrics(cases,rows):
    result={}
    for method in ('regex','ai'):
        predictions=[r[method] for r in rows]
        result[method]=score(cases,predictions)
        result[method]['raw_field_accuracy_including_nulls']={f:sum(fields_match({f:p.get('raw_fields',p['fields']).get(f)},{f:c['ground_truth_fields'].get(f)}) for c,p in zip(cases,predictions))/len(cases) for f in FIELDS}
        result[method]['rule_accuracy_evaluable_only']={}
        for rule in ('meal_limit','submission_window'):
            applicable=[(c,p) for c,p in zip(cases,predictions) if c['expected_checks'].get(rule) is not None]
            good=sum(next((x['pass'] for x in p['checks'] if x['rule']==rule),None)==c['expected_checks'][rule] for c,p in applicable)
            result[method]['rule_accuracy_evaluable_only'][rule]={'correct':good,'n':len(applicable),'rate':good/len(applicable) if applicable else None}
    return result


def report(cases,rows):
    selected=cases[:len(rows)]
    out={'planned_cases':len(cases),'attempted_cases':len(rows),'complete':len(rows)==len(cases),'headline_metrics':None}
    if not rows:return out
    values=metrics(selected,rows)
    out['headline_metrics' if out['complete'] else 'partial_metrics_not_final']=values
    out['groups']={}
    for dimension in ('group','source_type'):
        out['groups'][dimension]={}
        for group in sorted({c[dimension] for c in selected}):
            pairs=[(c,r) for c,r in zip(selected,rows) if c[dimension]==group]
            out['groups'][dimension][group]={'n':len(pairs),**metrics([p[0] for p in pairs],[p[1] for p in pairs])}
    # PASS was selected using development data, not the test distribution.
    out['fixed_development_majority_reference']={'label':'PASS','routing_correct':sum(c['expected_status']=='PASS' for c in selected),'n':len(selected),'note':'Routing-only baseline; no field extraction claimed.'}
    out['all_abstain']=evaluate(selected,[{'status':'ABSTAIN','fields':{}} for _ in selected])
    costs=[(r['log'].get('usage') or {}).get('cost') for r in rows]
    available=[x for x in costs if isinstance(x,(float,int)) and not isinstance(x,bool)]
    out['cost']={'reported_sum_usd':sum(available) if available else None,'records_available':len(available),'mean_usd':sum(available)/len(rows) if len(available)==len(rows) else None,'daily_80_receipts_estimate_usd':80*sum(available)/len(rows) if len(available)==len(rows) else None}
    out['latency_seconds']={m:sum(r[m+'_seconds'] for r in rows)/len(rows) for m in ('regex','ai')}
    out['service_failures']=sum(r['log'].get('connection_failed',False) for r in rows)
    return out


def main():
    try:manifest=verify()
    except (OSError,ValueError) as exc:print('Cannot run: '+str(exc));return 1
    if list((ROOT/'results').glob('final_*')):
        print('A final run already exists. Review it before any repeat; no request sent.');return 1
    inputs=json.loads((ROOT/'data/frozen_v1/inputs.json').read_text())
    labels=json.loads((ROOT/'data/frozen_v1/labels.json').read_text())
    cases=[{**x,**y} for x,y in zip(inputs,labels)]
    print('ReceiptGuard | FROZEN FINAL EVALUATION | 50 synthetic cases')
    print('Up to 50 paid AI requests. No retries. Results saved after every case.')
    print('Only receipt text is sent to the model; answers remain local.')
    if not sys.stdin.isatty():print('Open Run Final Evaluation.command in Terminal.');return 1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            key=getpass.getpass('Paste API key (invisible), then press Return: ').strip()
    except (EOFError,KeyboardInterrupt,getpass.GetPassWarning):print('\nCancelled.');return 1
    if not key:print('No key. No request sent.');return 1
    folder=ROOT/'results'/('final_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    (folder/'freeze_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=[];interrupted=False
    try:
        for case in cases:
            start=time.perf_counter()
            baseline=assess(validate_evidence(extract(case['receipt_text']),case['receipt_text']),case['claim_metadata'])
            regex_seconds=time.perf_counter()-start
            start=time.perf_counter()
            try:extraction,log=extract_ai(case['receipt_text'],key)
            except ConnectionProblem as exc:
                extraction={'fields':{f:None for f in FIELDS},'evidence':{},'issues':['service_failure']}
                log={'connection_failed':True,'message':str(exc),'attempts':1}
            prediction=assess(validate_evidence(extraction,case['receipt_text']),case['claim_metadata'])
            row={'case_id':case['case_id'],'regex':baseline,'ai':prediction,'log':log,'regex_seconds':regex_seconds,'ai_seconds':time.perf_counter()-start}
            rows.append(row)
            with (folder/'cases.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            print(f"{len(rows):02d}/50 | {case['case_id']} | Regex: {baseline['status']} | AI: {prediction['status']}")
            if log.get('connection_failed'):
                print(log['message']+' Stopping; remaining cases are not evaluated.');break
    except KeyboardInterrupt:
        interrupted=True;print('\nStopped. An in-flight call may incur cost without a saved response.')
    finally:
        key=None
        summary={'dataset_role':'FROZEN_SYNTHETIC_TEST_V1','interrupted':interrupted,**report(cases,rows)}
        (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('\n'+('FINAL RUN COMPLETE' if len(rows)==50 else 'PARTIAL RUN - NOT A FINAL SCORE'))
    print('Results: '+str(folder))
    return 0 if len(rows)==50 else 1

if __name__=='__main__':sys.exit(main())
