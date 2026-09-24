"""Shared evidence checks applied to both extractors before policy assessment."""
import re
from decimal import Decimal


def validate_evidence(extraction, text):
    issues = list(extraction.get('issues', []))
    fields = dict(extraction['fields'])
    evidence = extraction.get('evidence', {})
    for key in ('merchant', 'receipt_date', 'currency', 'total'):
        value = fields.get(key)
        if value is None:
            continue
        spans = evidence.get(key)
        spans = [spans] if isinstance(spans, str) else spans
        if not isinstance(spans, list) or not spans or any(not isinstance(s, str) or not s or s not in text for s in spans):
            issues.append('unsupported_evidence_' + key)
    for key, pattern in [('receipt_date', r'\d{4}-\d{2}-\d{2}'), ('total', r'\d+\.\d{2}'), ('currency', r'[A-Z]{3}')]:
        value = fields.get(key)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(pattern, value)):
            issues.append('invalid_' + key + '_format')
    # Check source ambiguity independently of either extractor's claim.
    currency_codes = set(re.findall(r"\b[A-Z]{3}\b", text.upper())) & {'SGD', 'USD', 'EUR', 'GBP', 'AUD', 'CAD', 'JPY', 'CNY', 'HKD', 'MYR'}
    if re.search(r"\bS\$", text, re.I):
        currency_codes.add('SGD')
    if len(currency_codes) != 1 or fields.get('currency') not in currency_codes:
        if fields.get('currency') is not None or len(currency_codes) > 1:
            issues.append('unresolved_currency')
        fields['currency'] = None
    # Only explicit final-total labels; subtotal/cash/change are not candidates.
    pattern = r"^[ \t]*(?:grand total|total|amount due|balance due)[ \t]*:?[ \t]*(?:(?:SGD|USD|EUR|S\$|\$)[ \t]*)?(\d+(?:,\d{3})*\.\d{2})[ \t]*$"
    totals = {Decimal(x.replace(',', '')) for x in re.findall(pattern, text, re.I | re.M)}
    if len(totals) > 1:
        fields['total'] = None
        issues.append('conflicting_explicit_totals')
    normalized_evidence = dict(evidence)
    for key, value in fields.items():
        if value is None:
            normalized_evidence[key] = None
    return {**extraction, 'fields': fields, 'evidence': normalized_evidence,
            'raw_fields': dict(extraction.get('raw_fields', extraction['fields'])),
            'validation_version': 'shared-v0.2', 'issues': sorted(set(issues))}
