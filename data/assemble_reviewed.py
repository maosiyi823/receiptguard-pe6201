"""Assemble reviewed candidates without querying either extractor.
Review is by the implementation assistant, NOT an independent human reviewer.
"""
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).parent
SOURCE=ROOT/'independent/20260924T121556999530Z'

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    base_inputs=read(ROOT/'test_candidate_inputs.json');base_labels=read(ROOT/'test_candidate_labels.json')
    # Predeclared first 12 per main group + first 4 insufficient cases.
    indexes=list(range(12))+list(range(15,27))+list(range(30,42))+list(range(45,49))
    inputs=[base_inputs[i] for i in indexes]
    labels=[base_labels[i] for i in indexes]
    changes=[]
    external_inputs=read(SOURCE/'inputs.json');external_labels=read(SOURCE/'proposed_labels.json')
    for x,y in zip(external_inputs,external_labels):
        original=json.loads(json.dumps(y))
        ident=y['case_id']
        if ident=='independent-002':
            y['annotation_note']='SGD 15.75 is within the amount limit, but 35 days elapsed from 2026-08-20 to 2026-09-24. FLAG for lateness, not amount.'
        if ident=='independent-005':
            y['expected_status']='PASS'
            y['annotation_note']='SGD 35.00 is below 50.00; submission is 23 days later. Both rules pass.'
        if ident=='independent-007':
            y['group']='clean_varied'
            y['annotation_note']='S$ is a normal SGD marker, not OCR corruption. Total is 9.40 and submission is 2 days later.'
        if ident in ('independent-008','independent-009'):
            y['group']='distractors'
            y['annotation_note']+=' No actual OCR corruption is present; grouped as distractor text.'
        if ident=='independent-010':
            y['annotation_note']='No currency is given. Price: 5.00 is an item price without an explicit final total; under the no-inferred-total annotation convention, total remains null. ABSTAIN.'
        for key in ('expected_status','group','annotation_note'):
            if original[key]!=y[key]:changes.append({'case_id':ident,'field':key,'original':original[key],'reviewed':y[key]})
        inputs.append(x);labels.append(y)
    assert len(inputs)==len(labels)==50
    review=[]
    for x,y in zip(inputs,labels):
        assert x['case_id']==y['case_id']
        f=y['ground_truth_fields']
        amount=Decimal(f['total']) if f['total'] is not None else None
        age=(date.fromisoformat(x['claim_metadata']['submission_date'])-date.fromisoformat(f['receipt_date'])).days if f['receipt_date'] else None
        checks={'meal_limit':amount<=Decimal('50') if amount is not None else None,'submission_window':0<=age<=30 if age is not None else None}
        expected='ABSTAIN' if any(f[k] is None for k in ('total','currency','receipt_date')) or f['currency']!='SGD' else ('FLAG' if not all(checks.values()) else 'PASS')
        assert expected==y['expected_status'],x['case_id']
        assert amount is None or amount>0
        y['expected_checks']=checks
        y['review_status']='assistant_reviewed_not_human_verified'
        review.append({'case_id':x['case_id'],'age_days':age,'total':f['total'],'currency':f['currency'],'expected_status':expected,'expected_checks':checks})
    dest=ROOT/'reviewed';dest.mkdir(exist_ok=True)
    for name,obj in [('inputs.json',inputs),('labels.json',labels),('label_corrections.json',changes),('arithmetic_audit.json',review)]:
        (dest/name).write_text(json.dumps(obj,indent=2)+'\n')
    manifest={'status':'REVIEWED_CANDIDATE_NOT_FROZEN','count':50,'source_counts':dict(Counter(y['source_type'] for y in labels)),'group_counts':dict(Counter(y['group'] for y in labels)),'status_counts':dict(Counter(y['expected_status'] for y in labels)), 'reviewer':'implementation assistant; not independent human verification', 'model_evaluation_performed':False,'independent_generation_record_sha256':digest(SOURCE/'generation_record.json'),'inputs_sha256':digest(dest/'inputs.json'),'labels_sha256':digest(dest/'labels.json'),'correction_count':len(changes)}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
