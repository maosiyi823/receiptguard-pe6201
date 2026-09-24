"""One synthetic receipt, one real request. Never stores the API key."""
import getpass
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from ai_client import extract_ai, ConnectionProblem, MODEL
from receiptguard import assess, extract, fields_match
from common_validation import validate_evidence

TEXT = 'Merchant: Demo Cafe\nDate: 2026-09-20\nCurrency: SGD\nTotal: 12.50'
META = {'claim_category': 'meal', 'submission_date': '2026-09-24'}

def main():
    print('ReceiptGuard | First real AI connection\n')
    print('This sends ONE synthetic receipt to OpenRouter using ' + MODEL + '.')
    print('A successful request may use paid credits. No automatic retries.')
    print('Your API key will not be displayed or saved.\n')
    print(TEXT + '\n')
    if not sys.stdin.isatty():
        print('Please open Start ReceiptGuard.command in Terminal. No request sent.')
        return 1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            key = getpass.getpass('Paste your API key here (invisible), then press Return: ').strip()
        if not key:
            print('No key entered. No request sent.')
            return 1
        print('\nConnecting... Please wait up to 45 seconds.')
        extraction, log = extract_ai(TEXT, key)
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print('\nCancelled. Hidden key entry is required.')
        return 1
    except ConnectionProblem as exc:
        print('\nCONNECTION NOT COMPLETED\n' + str(exc))
        return 1
    finally:
        key = None
    result = assess(validate_evidence(extraction, TEXT), META)
    expected = {'receipt_date':'2026-09-20','currency':'SGD','total':'12.50'}
    passed = result['status'] == 'PASS' and fields_match(result['fields'], expected)
    record = {'run_type': 'single_synthetic_development_check_not_final_evaluation', 'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'receipt_text': TEXT, 'claim_metadata': META, 'ai_result': result, 'regex_result': assess(validate_evidence(extract(TEXT), TEXT), META), 'connection_log': log, 'sample_check_passed': passed}
    out = Path(__file__).parent / 'results' / ('first_ai_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print('\nAPI RESPONSE RECEIVED')
    print('Sample check: ' + ('PASSED' if passed else 'NEEDS REVIEW'))
    print('Decision: ' + result['status'])
    print('Extracted fields: ' + json.dumps(result['fields']))
    print('Results saved to: ' + str(out))
    print('This is one development example, not a final accuracy score.')
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
