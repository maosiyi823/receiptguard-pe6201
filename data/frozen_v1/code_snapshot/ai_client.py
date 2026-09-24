"""OpenRouter extraction with strict local validation and no credential logging."""
import hashlib
import json
import re
import time
from pathlib import Path
from urllib import request, error

MODEL = 'openai/gpt-4o-mini'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
KEYS = ('merchant', 'receipt_date', 'currency', 'total')
PROMPT = Path(__file__).with_name('prompts').joinpath('extract_v2.txt').read_text()
NULLABLE = {'type': ['string', 'null']}
FIELD_SCHEMA = {'type': 'object', 'properties': {k: NULLABLE for k in KEYS}, 'required': list(KEYS), 'additionalProperties': False}
SCHEMA = {'type': 'object', 'properties': {'fields': FIELD_SCHEMA, 'evidence': FIELD_SCHEMA, 'issues': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['fields', 'evidence', 'issues'], 'additionalProperties': False}

class ConnectionProblem(Exception):
    """Only safe, predefined messages are surfaced to users."""


def validate(value, text):
    if not isinstance(value, dict) or set(value) != {'fields', 'evidence', 'issues'}:
        raise ValueError('Invalid extraction shape')
    for name in ('fields', 'evidence'):
        obj = value[name]
        if not isinstance(obj, dict) or set(obj) != set(KEYS):
            raise ValueError('Invalid field set')
        if any(v is not None and not isinstance(v, str) for v in obj.values()):
            raise ValueError('Invalid field type')
    if not isinstance(value['issues'], list) or any(not isinstance(x, str) for x in value['issues']):
        raise ValueError('Invalid issue list')
    fields, evidence = value['fields'], value['evidence']
    issues = list(value['issues'])
    for key in KEYS:
        if fields[key] is not None and (not evidence[key] or evidence[key] not in text):
            issues.append('unsupported_evidence_' + key)
    if fields['total'] is not None and not re.fullmatch(r'\d+\.\d{2}', fields['total']):
        issues.append('invalid_total_format')
    if fields['receipt_date'] is not None and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fields['receipt_date']):
        issues.append('invalid_date_format')
    if fields['currency'] is not None and not re.fullmatch(r'[A-Z]{3}', fields['currency']):
        issues.append('invalid_currency_format')
    return {'fields': fields, 'evidence': evidence, 'issues': sorted(set(issues))}


def extract_ai(text, api_key, opener=None):
    if not api_key or not api_key.isascii() or any(c.isspace() for c in api_key):
        raise ConnectionProblem('Invalid key format. Copy the key again without spaces.')
    body = {'model': MODEL, 'temperature': 0, 'max_tokens': 600,
            'provider': {'require_parameters': True},
            'messages': [{'role': 'system', 'content': PROMPT}, {'role': 'user', 'content': json.dumps({'receipt_text': text})}],
            'response_format': {'type': 'json_schema', 'json_schema': {'name': 'receipt', 'strict': True, 'schema': SCHEMA}}}
    req = request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, method='POST')
    started = time.perf_counter()
    try:
        with (opener or request.urlopen)(req, timeout=45) as response:
            payload = json.loads(response.read())
    except error.HTTPError as exc:
        messages = {401: 'The API key was not accepted.', 402: 'The service reports insufficient credits. No retry was made.', 429: 'Rate limit reached. No retry was made.', 400: 'The request or structured-output settings were rejected.', 403: 'The service denied access.'}
        raise ConnectionProblem(messages.get(exc.code, 'The service returned HTTP ' + str(exc.code) + '. No retry was made.')) from None
    except (error.URLError, TimeoutError, OSError):
        raise ConnectionProblem('Connection failed or timed out. No automatic retry was made; check service usage before trying again.') from None
    except (ValueError, UnicodeError):
        raise ConnectionProblem('The service returned an unreadable response.') from None
    elapsed = round(time.perf_counter() - started, 3)
    log = {'requested_model': MODEL, 'temperature': 0, 'max_tokens': 600, 'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest(), 'latency_seconds': elapsed, 'attempts': 1}
    try:
        log.update({'returned_model': payload.get('model'), 'request_id': payload.get('id'), 'usage': payload.get('usage')})
        choice = payload['choices'][0]
        content = choice['message']['content']
        if choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
            raise ValueError('Incomplete response')
        log['raw_model_output'] = content
        extraction = validate(json.loads(content), text)
        log['output_valid'] = True
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        extraction = {'fields': {k: None for k in KEYS}, 'evidence': {}, 'issues': ['invalid_model_output']}
        log['output_valid'] = False
    return extraction, log
