import io
import json
import unittest
from urllib.error import HTTPError, URLError
from ai_client import extract_ai, validate, ConnectionProblem
from receiptguard import assess

TEXT='Date: 2026-09-20\nSGD\nTotal: 12.50'
def valid():
    return {'fields':{'merchant':None,'receipt_date':'2026-09-20','currency':'SGD','total':'12.50'},'evidence':{'merchant':None,'receipt_date':'2026-09-20','currency':'SGD','total':'12.50'},'issues':[]}
def response(content, finish='stop'):
    return io.BytesIO(json.dumps({'model':'test-model','choices':[{'finish_reason':finish,'message':{'content':content}}],'usage':{'prompt_tokens':10,'completion_tokens':20}}).encode())

class AIClientTests(unittest.TestCase):
    def test_request_excludes_answers_and_logs_exclude_key(self):
        def opener(req, timeout):
            body=json.loads(req.data)
            self.assertEqual(body['temperature'],0)
            self.assertTrue(body['provider']['require_parameters'])
            self.assertEqual(json.loads(body['messages'][1]['content']),{'receipt_text':TEXT})
            return response(json.dumps(valid()))
        output,log=extract_ai(TEXT,'unit-test-key',opener)
        self.assertNotIn('unit-test-key',json.dumps(log))
        self.assertEqual(output['fields']['total'],'12.50')
    def test_bad_output_fails_closed(self):
        out,log=extract_ai(TEXT,'test',lambda *a,**k:response('not json'))
        self.assertFalse(log['output_valid'])
        self.assertEqual(assess(out,{'claim_category':'meal','submission_date':'2026-09-24'})['status'],'ABSTAIN')
    def test_truncated_output_rejected(self):
        out,log=extract_ai(TEXT,'test',lambda *a,**k:response(json.dumps(valid()),'length'))
        self.assertFalse(log['output_valid'])
    def test_evidence_missing_from_input(self):
        value=valid();value['evidence']['total']='99.00'
        self.assertIn('unsupported_evidence_total',validate(value,TEXT)['issues'])
    def test_wrong_type_rejected(self):
        value=valid();value['fields']['total']=12.5
        with self.assertRaises(ValueError):validate(value,TEXT)
    def test_credit_error_safe_and_no_retry(self):
        calls=[]
        def opener(*a,**k):
            calls.append(1)
            raise HTTPError('https://example.invalid',402,'secret response',{},None)
        with self.assertRaisesRegex(ConnectionProblem,'insufficient credits'):
            extract_ai(TEXT,'unit-test-key',opener)
        self.assertEqual(len(calls),1)
    def test_network_failure_safe(self):
        def opener(*a,**k):raise URLError('sensitive debug')
        with self.assertRaisesRegex(ConnectionProblem,'Connection failed'):
            extract_ai(TEXT,'test',opener)

if __name__=='__main__':unittest.main()
