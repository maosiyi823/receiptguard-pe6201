"""Offline teaching prototype. No model calls or OCR are performed."""
import argparse
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ('receipt_date', 'currency', 'total')


def extract(text):
    values = {k: None for k in ('merchant', *FIELDS)}
    evidence = {}
    issues = []
    patterns = {
        'merchant': r'^\s*(?:merchant|store)\s*:\s*(.+?)\s*$',
        'receipt_date': r'^\s*(?:date|receipt date)\s*:\s*(\d{4}-\d{2}-\d{2})\s*$',
        'total': r'^\s*(?:grand total|total|amount due|balance due)\s*:?\s*(?:(?:SGD|USD|EUR|S\$|\$)\s*)?(\d+(?:,\d{3})*\.\d{2})\s*$',
    }
    for key, pattern in patterns.items():
        matches = list(re.finditer(pattern, text, re.I | re.M))
        candidates = {m.group(1).strip().replace(',', '') if key == 'total' else m.group(1).strip() for m in matches}
        if len(candidates) == 1:
            values[key] = candidates.pop()
            evidence[key] = [m.group(0).strip() for m in matches]
        elif len(candidates) > 1:
            issues.append('ambiguous_' + key)
    currencies = set(re.findall(r'\b(?:SGD|USD|EUR)\b', text.upper()))
    if re.search(r'\bS\$', text, re.I):
        currencies.add('SGD')
    if len(currencies) == 1:
        values['currency'] = currencies.pop()
        evidence['currency'] = [s for s in text.splitlines() if re.search(r'\b(?:SGD|USD|EUR)\b|\bS\$', s, re.I)]
    elif len(currencies) > 1:
        issues.append('ambiguous_currency')
    return {'fields': values, 'evidence': evidence, 'issues': issues}


def assess(extraction, metadata):
    fields = extraction['fields']
    reasons = list(extraction.get('issues', []))
    checks = []
    for field in FIELDS:
        if fields.get(field) is None:
            reasons.append('missing_' + field)
    if fields.get('currency') not in (None, 'SGD'):
        reasons.append('unsupported_currency')
    if metadata.get('claim_category') != 'meal':
        reasons.append('unsupported_or_missing_category')
    if fields.get('total') is not None:
        try:
            amount = Decimal(str(fields['total']))
            if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal('.01')):
                raise ValueError('invalid money')
            checks.append({'rule': 'meal_limit', 'pass': amount <= Decimal('50.00')})
        except (InvalidOperation, ValueError):
            reasons.append('invalid_total')
    if fields.get('receipt_date') is not None:
        try:
            day = date.fromisoformat(fields['receipt_date'])
            submitted = date.fromisoformat(metadata['submission_date'])
            age = (submitted - day).days
            checks.append({'rule': 'submission_window', 'pass': 0 <= age <= 30, 'age_days': age})
        except (ValueError, TypeError, KeyError):
            reasons.append('invalid_or_missing_date')
    status = 'ABSTAIN' if reasons else ('FLAG' if any(not c['pass'] for c in checks) else 'PASS')
    return {**extraction, 'checks': checks, 'status': status, 'review_required': status != 'PASS', 'review_reasons': sorted(set(reasons)), 'policy_version': 'demo-v0.1'}


def fields_match(actual, expected):
    for key in FIELDS:
        a, b = actual.get(key), expected.get(key)
        if key == 'total' and a is not None and b is not None:
            try:
                if Decimal(str(a)) != Decimal(str(b)):
                    return False
            except InvalidOperation:
                return False
        elif a != b:
            return False
    return True


def evaluate(cases, predictions):
    if len(cases) != len(predictions) or not cases:
        raise ValueError('Require nonempty matching inputs and predictions')
    n = len(cases)
    answered = sum(p['status'] != 'ABSTAIN' for p in predictions)
    correct = sum(p['status'] != 'ABSTAIN' and p['status'] == c['expected_status'] and fields_match(p['fields'], c['ground_truth_fields']) for c, p in zip(cases, predictions))
    flags = sum(c['expected_status'] == 'FLAG' for c in cases)
    abstains = sum(c['expected_status'] == 'ABSTAIN' for c in cases)
    return {
        'n': n, 'correct_automated_count': correct,
        'end_to_end_correct_rate': correct / n, 'coverage': answered / n,
        'abstention_rate': (n - answered) / n,
        'answered_accuracy': correct / answered if answered else None,
        'routing_accuracy': sum(c['expected_status'] == p['status'] for c,p in zip(cases,predictions)) / n,
        'violation_recall': sum(c['expected_status'] == 'FLAG' and p['status'] == 'FLAG' for c,p in zip(cases,predictions)) / flags if flags else None,
        'false_release_count': sum(c['expected_status'] != 'PASS' and p['status'] == 'PASS' for c,p in zip(cases,predictions)),
        'required_abstention_recall': sum(c['expected_status'] == 'ABSTAIN' and p['status'] == 'ABSTAIN' for c,p in zip(cases,predictions)) / abstains if abstains else None,
        'over_abstention_count': sum(c['expected_status'] != 'ABSTAIN' and p['status'] == 'ABSTAIN' for c,p in zip(cases,predictions)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='data/dev.json')
    parser.add_argument('--output', default='results/dev_regex.json')
    args = parser.parse_args()
    cases = json.loads(Path(args.data).read_text())
    predictions = [assess(extract(c['receipt_text']), c['claim_metadata']) for c in cases]
    abstain_predictions = [{'status': 'ABSTAIN', 'fields': {}} for _ in cases]
    report = {'dataset_role': 'DEVELOPMENT_ONLY_NOT_FINAL_TEST', 'method': 'regex', 'metrics': evaluate(cases, predictions), 'all_abstain_reference': evaluate(cases, abstain_predictions), 'cases': [{'case_id': c['case_id'], 'expected_status': c['expected_status'], 'prediction': p} for c,p in zip(cases,predictions)]}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': args.output, 'dataset_role': report['dataset_role'], 'metrics': report['metrics']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
