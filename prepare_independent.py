"""Request a different model's candidate cases. Does not evaluate or freeze them."""
import getpass
import hashlib
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error

ROOT=Path(__file__).parent
MODEL='google/gemini-2.5-flash-lite'
PROMPT_PATH=ROOT/'prompts/independent_cases_v1.txt'
PROPERTIES={k:{'type':'string'} for k in ['receipt_text','claim_category','submission_date','group','expected_status','annotation_note']}
PROPERTIES.update({k:{'type':['string','null']} for k in ['receipt_date','currency','total']})
SCHEMA={'type':'object','properties':{'cases':{'type':'array','items':{'type':'object','properties':PROPERTIES,'required':list(PROPERTIES),'additionalProperties':False}}},'required':['cases'],'additionalProperties':False}

def check_shape(data):
    if not isinstance(data,dict) or set(data)!={'cases'} or not isinstance(data['cases'],list) or len(data['cases'])!=10:
        raise ValueError('Expected exactly 10 cases')
    for i,c in enumerate(data['cases']):
        if not isinstance(c,dict) or set(c)!=set(PROPERTIES):raise ValueError('Invalid fields')
        for k in PROPERTIES:
            if not isinstance(c[k],str) and not (k in ['receipt_date','currency','total'] and c[k] is None):raise ValueError('Invalid types')
        group=['clean_varied']*3+['distractors']*3+['simulated_ocr']*3+['insufficient_information']
        if c['group']!=group[i]:raise ValueError('Incorrect group order')
        if c['expected_status']!=('ABSTAIN' if i==9 else 'PASS' if i%3==0 else 'FLAG'):raise ValueError('Incorrect planned status distribution')
        if c['claim_category']!='meal' or c['submission_date']!='2026-09-24':raise ValueError('Unexpected metadata')
        if not c['receipt_text'].strip() or not c['annotation_note'].strip():raise ValueError('Empty content')
    if len({c['receipt_text'] for c in data['cases']})!=10:raise ValueError('Duplicate receipts')
    return data

def main():
    print('ReceiptGuard | Prepare independently contributed candidate cases')
    print('One request to '+MODEL+'. Paid usage may apply; no retries.')
    print('Only a task specification is sent. No files, existing cases or API keys enter the prompt.')
    print('Output requires review. This does NOT run a final evaluation.\n')
    if not sys.stdin.isatty():print('Open Prepare Test Data.command in Terminal.');return 1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            key=getpass.getpass('Paste API key (invisible), then press Return: ').strip()
    except (EOFError,KeyboardInterrupt,getpass.GetPassWarning):print('\nCancelled.');return 1
    if not key or not key.isascii() or any(c.isspace() for c in key):print('Invalid or missing key. No request sent.');return 1
    prompt=PROMPT_PATH.read_text()
    body={'model':MODEL,'temperature':0,'max_tokens':7000,'provider':{'require_parameters':True},'messages':[{'role':'user','content':prompt}], 'response_format':{'type':'json_schema','json_schema':{'name':'candidate_receipts','strict':True,'schema':SCHEMA}}}
    req=request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'data'/'independent'/stamp;folder.mkdir(parents=True)
    start=time.perf_counter()
    print('Generating 10 candidates... Please wait up to 60 seconds.')
    try:
        with request.urlopen(req,timeout=60) as response:payload=json.loads(response.read())
    except error.HTTPError as exc:
        print('Service returned HTTP '+str(exc.code)+'. No retry made.');return 1
    except (error.URLError,OSError,ValueError):
        print('Connection or response failed. No retry made.');return 1
    except KeyboardInterrupt:
        print('\nStopped. Check service usage before repeating.');return 1
    finally:key=None
    record={'status':'UNREVIEWED_NOT_FROZEN','requested_model':MODEL,'returned_model':payload.get('model') if isinstance(payload,dict) else None,'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'latency_seconds':round(time.perf_counter()-start,3),'response':payload}
    (folder/'generation_record.json').write_text(json.dumps(record,indent=2)+'\n')
    try:
        choice=payload['choices'][0]
        if choice.get('finish_reason')!='stop':raise ValueError('Incomplete output')
        cases=check_shape(json.loads(choice['message']['content']))['cases']
    except (KeyError,IndexError,TypeError,ValueError):
        print('Response saved, but candidate validation failed. Ask for review; do not regenerate yet.');print(folder);return 1
    inputs=[];labels=[]
    for i,c in enumerate(cases,1):
        ident=f'independent-{i:03d}'
        inputs.append({'case_id':ident,'receipt_text':c['receipt_text'],'claim_metadata':{'claim_category':c['claim_category'],'submission_date':c['submission_date']}})
        labels.append({'case_id':ident,'group':c['group'],'source_type':'synthetic_other_model','ground_truth_fields':{k:c[k] for k in ['receipt_date','currency','total']},'expected_status':c['expected_status'],'annotation_note':c['annotation_note'],'review_status':'pending','generator_model':MODEL})
    for name,value in [('inputs.json',inputs),('proposed_labels.json',labels)]:
        (folder/name).write_text(json.dumps(value,indent=2)+'\n')
    print('10 CANDIDATES SAVED. Their answers still require review.')
    print('Saved to: '+str(folder))
    return 0

if __name__=='__main__':sys.exit(main())
