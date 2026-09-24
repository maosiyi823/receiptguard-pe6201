"""Generate reproducible synthetic test CANDIDATES, not an independently reviewed test set.
No extractor or policy implementation is imported and no predictions are examined.
"""
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
SEED = 62012026
rng = random.Random(SEED)
inputs, labels = [], []
for i in range(50):
    group = 'clean_varied' if i < 15 else 'distractors' if i < 30 else 'simulated_ocr' if i < 45 else 'insufficient_information'
    local = i % 15
    scenario = local % 3
    # Design labels before creating the presentation. Independently reviewed labels are still needed.
    cents = rng.randint(800, 4800) if scenario != 1 else rng.randint(5100, 8500)
    age = rng.randint(1, 29) if scenario != 2 else rng.randint(31, 45)
    submitted = date(2026, 9, 24)
    day = (submitted - timedelta(days=age)).isoformat()
    amount = f'{cents / 100:.2f}'
    merchant = f'Practice Kitchen {i + 1:02d}'
    fields = {'receipt_date': day, 'currency': 'SGD', 'total': amount}
    total_label = ['Total', 'Grand Total', 'Amount Due'][local % 3]
    text = f'Merchant: {merchant}\nDate: {day}\nCurrency: SGD\n{total_label}: {amount}'
    noise = 'none'
    expected = 'PASS' if scenario == 0 else 'FLAG'
    note = 'Within the amount limit and submission window.' if scenario == 0 else 'Amount exceeds SGD 50.00.' if scenario == 1 else 'Submitted more than 30 days after the receipt date.'
    rules = {'meal_limit': cents <= 5000, 'submission_window': 0 <= age <= 30}
    if group == 'clean_varied':
        if local % 3 == 1:
            text = f'Store: {merchant}\nReceipt date: {day}\n{total_label}: SGD {amount}'
        elif local % 3 == 2:
            text = f'Merchant: {merchant}\nDate: {day}\nSGD\n{total_label}\n{amount}'
    elif group == 'distractors':
        # Synthetic amount components are not claims about actual tax rates.
        tax = max(1, cents // 12)
        text = f'Merchant: {merchant}\nDate: {day}\nCurrency: SGD\nSubtotal: {(cents-tax)/100:.2f}\nTax: {tax/100:.2f}\n{total_label}: {amount}\nCash: 100.00\nChange: {(10000-cents)/100:.2f}\nReference: {rng.randint(100000,999999)}'
    elif group == 'simulated_ocr':
        mode = local % 5
        if mode == 0:
            text = text.replace(total_label, 'T0TAL'); noise = 'total_label_O_to_zero'
        elif mode == 1:
            text = text.replace(': ', ' :    '); noise = 'extra_spacing'
        elif mode == 2:
            text = text.replace(f'{total_label}: {amount}', f'{total_label}:\n{amount}'); noise = 'line_break_before_total'
        elif mode == 3:
            text = text.replace('Date:', 'Receipt date:').replace(total_label, 'TOTAL').replace('Merchant:', 'MERCHANT:'); noise = 'case_and_label_variation'
        else:
            text = text.replace('\n', '   |   '); noise = 'flattened_reading_order'
    else:
        # Each case has genuinely insufficient information, not just an unfamiliar label.
        expected = 'ABSTAIN'
        if i == 45:
            text = f'Merchant: {merchant}\nDate: {day}\nCurrency: SGD\nTotal: [unreadable]'
            fields['total'] = None; rules['meal_limit'] = None
            note = 'The provided text does not reveal the total.'; noise = 'total_erased'
        elif i == 46:
            text = f'Merchant: {merchant}\nDate: {day}\nTotal: ${amount}'
            fields['currency'] = None
            note = 'A bare dollar symbol does not establish SGD.'; noise = 'currency_code_erased'
        elif i == 47:
            text = f'Merchant: {merchant}\nCurrency: SGD\nTotal: {amount}'
            fields['receipt_date'] = None; rules['submission_window'] = None
            note = 'The receipt date is absent.'; noise = 'date_erased'
        elif i == 48:
            text += f'\nTotal: {(cents+700)/100:.2f}'
            fields['total'] = None; rules['meal_limit'] = None
            note = 'Two conflicting totals have no identifying context.'; noise = 'conflicting_totals'
        else:
            text += '\nCurrency: USD'
            fields['currency'] = None
            note = 'Two conflicting currency codes have no identifying context.'; noise = 'conflicting_currency'
    case_id = f'candidate-{i+1:03d}'
    inputs.append({'case_id':case_id, 'receipt_text':text, 'claim_metadata':{'claim_category':'meal','submission_date':submitted.isoformat()}})
    labels.append({'case_id':case_id,'source_type':'synthetic','group':group,'noise_type':noise,'base_receipt_id':case_id,'ground_truth_fields':fields,'expected_status':expected,'expected_checks':rules,'annotation_note':note,'review_status':'pending_independent_review'})

def save(name, value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    (ROOT/name).write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

hashes={name:save(name,value) for name,value in [('test_candidate_inputs.json',inputs),('test_candidate_labels.json',labels)]}
save('test_candidate_manifest.json',{'status':'CANDIDATE_NOT_FROZEN','seed':SEED,'count':50,'origin':'Deterministic Python generator authored by the implementation assistant; not independent holdout authorship.','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'file_sha256':hashes,'real_receipts':0,'evaluation_run':False,'limitations':['Simulated text noise only; no real OCR pipeline validated.','Independent case authorship and human label review remain outstanding.','Do not tune the parser or prompt using these candidates and then claim them as unseen data.']})
print('Wrote 50 synthetic candidates and separate labels. NOT frozen; NOT evaluated.')
