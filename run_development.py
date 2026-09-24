"""Run the complete DEVELOPMENT set, checkpointing every case. Not final evaluation."""
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
from receiptguard import extract, assess, evaluate, FIELDS, fields_match

ROOT = Path(__file__).parent

def score(cases, predictions):
    result = evaluate(cases, predictions)
    result['field_accuracy_including_nulls'] = {
        f: sum(fields_match({f:p['fields'].get(f)}, {f:c['ground_truth_fields'].get(f)}) for c,p in zip(cases,predictions))/len(cases) for f in FIELDS
    }
    result['human_review_rate'] = sum(p['status'] != 'PASS' for p in predictions)/len(cases)
    return result


def summarize(cases, rows):
    completed = cases[:len(rows)]
    if not rows:
        return {'completed': 0, 'planned': len(cases)}
    usage = [r['log'].get('usage') or {} for r in rows]
    costs = [u.get('cost') for u in usage]
    numeric_costs = [v for v in costs if isinstance(v,(float,int)) and not isinstance(v,bool)]
    counts = {s:sum(c['expected_status']==s for c in cases) for s in ('PASS','FLAG','ABSTAIN')}
    majority = max(counts,key=counts.get)
    return {'completed':len(rows),'planned':len(cases),'complete':len(rows)==len(cases),
        'regex':score(completed,[r['regex'] for r in rows]),
        'ai':score(completed,[r['ai'] for r in rows]),
        'service_failure_count':sum(r['log'].get('connection_failed',False) for r in rows),
        'reported_cost_sum_usd':sum(numeric_costs) if numeric_costs else None,
        'cost_records_available':len(numeric_costs),
        'mean_reported_cost_usd':sum(numeric_costs)/len(rows) if len(numeric_costs)==len(rows) else None,
        'daily_model_cost_at_80_receipts_usd':80*sum(numeric_costs)/len(rows) if len(numeric_costs)==len(rows) else None,
        'mean_ai_attempt_seconds':sum(r['elapsed_seconds'] for r in rows)/len(rows),
        'development_majority_label':majority,
        'majority_routing_accuracy':sum(c['expected_status']==majority for c in completed)/len(completed),
        'all_abstain':evaluate(completed,[{'status':'ABSTAIN','fields':{}} for _ in rows])}


def main():
    print('ReceiptGuard | Development comparison (14 examples, NOT final evaluation)')
    print('Sends 14 synthetic receipts to OpenRouter, one request per case. Paid usage may apply.')
    print('No retries. Each result is saved immediately. Press Ctrl+C to stop.\n')
    if not sys.stdin.isatty():
        print('Open Run Development.command in Terminal. No requests sent.'); return 1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            key=getpass.getpass('Paste API key (invisible), then press Return: ').strip()
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print('\nCancelled.'); return 1
    if not key:
        print('No key. No requests sent.'); return 1
    cases=json.loads((ROOT/'data/dev.json').read_text())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'results'/('development_'+stamp);folder.mkdir()
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['data/dev.json','prompts/extract_v2.txt','receiptguard.py','ai_client.py','common_validation.py','run_development.py']}
    rows=[]
    interrupted=False
    try:
        for case in cases:
            baseline=assess(validate_evidence(extract(case['receipt_text']),case['receipt_text']),case['claim_metadata'])
            start=time.perf_counter()
            try:
                extracted,log=extract_ai(case['receipt_text'],key)
            except ConnectionProblem as exc:
                extracted={'fields':{f:None for f in FIELDS},'evidence':{},'issues':['service_failure']}
                log={'connection_failed':True,'message':str(exc),'attempts':1}
            prediction=assess(validate_evidence(extracted,case['receipt_text']),case['claim_metadata'])
            row={'case_id':case['case_id'],'regex':baseline,'ai':prediction,'log':log,'elapsed_seconds':round(time.perf_counter()-start,3)}
            rows.append(row)
            with (folder/'cases.jsonl').open('a') as handle:handle.write(json.dumps(row)+'\n')
            print(f"{len(rows):02d}/{len(cases)} | {case['case_id']} | Regex: {baseline['status']} | AI: {prediction['status']}")
            if log.get('connection_failed'):
                print(log['message']); print('Stopping to avoid repeated failed requests. Remaining cases are NOT evaluated.');break
    except KeyboardInterrupt:
        interrupted=True
        print('\nStopped. An in-flight request may have incurred cost without a saved result.')
    finally:
        key=None
        report={'dataset_role':'DEVELOPMENT_ONLY','interrupted':interrupted,'hashes':hashes,'summary':summarize(cases,rows)}
        (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('\nSaved results: '+str(folder))
    print('Finished '+str(len(rows))+' of '+str(len(cases))+' cases. These are development results only.')
    return 0 if len(rows)==len(cases) else 1

if __name__=='__main__':sys.exit(main())
