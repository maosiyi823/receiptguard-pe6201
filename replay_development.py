"""Offline replay of archived outputs through new validation. No API requests."""
import hashlib
import json
from pathlib import Path
from common_validation import validate_evidence
from receiptguard import assess
from run_development import score

ROOT=Path(__file__).parent
SOURCE=ROOT/'results/development_20260924T120434935194Z/cases.jsonl'

def main():
    cases=json.loads((ROOT/'data/dev.json').read_text())
    old={r['case_id']:r for r in map(json.loads,SOURCE.read_text().splitlines())}
    rows=[]
    for c in cases:
        row={'case_id':c['case_id']}
        for method in ('regex','ai'):
            prior=old[c['case_id']][method]
            extraction={k:prior[k] for k in ('fields','evidence','issues')}
            row[method]=assess(validate_evidence(extraction,c['receipt_text']),c['claim_metadata'])
        rows.append(row)
    report={'experiment_type':'OFFLINE_REPLAY_OF_V1_OUTPUTS_NOT_A_NEW_MODEL_RUN',
        'source_file':str(SOURCE.relative_to(ROOT)), 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'validator_sha256':hashlib.sha256((ROOT/'common_validation.py').read_bytes()).hexdigest(),
        'prompt_v2_tested':False,'new_api_calls':0,
        'metrics':{m:score(cases,[r[m] for r in rows]) for m in ('regex','ai')},'cases':rows}
    out=ROOT/'results/development_v1_outputs_validation_v02_replay.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('experiment_type','new_api_calls','metrics')},indent=2))

if __name__=='__main__':main()
