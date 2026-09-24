import unittest
from common_validation import validate_evidence
from receiptguard import extract, assess
from run_development import summarize

class DevelopmentTests(unittest.TestCase):
    def test_shared_validation_accepts_regex_evidence(self):
        text='Date: 2026-09-20\nSGD\nTotal: 12.50'
        self.assertEqual(validate_evidence(extract(text),text)['issues'],[])
    def test_shared_validation_rejects_unfounded_evidence(self):
        x={'fields':{'total':'12.50'},'evidence':{'total':['99.99']},'issues':[]}
        self.assertIn('unsupported_evidence_total',validate_evidence(x,'Total: 12.50')['issues'])
    def test_partial_run_and_missing_cost_not_zero(self):
        c={'expected_status':'PASS','ground_truth_fields':{'receipt_date':'2026-09-20','currency':'SGD','total':'12.50'}}
        prediction={'status':'ABSTAIN','fields':{}}
        r=summarize([c,c],[{'regex':prediction,'ai':prediction,'log':{'connection_failed':True},'elapsed_seconds':1}])
        self.assertFalse(r['complete']);self.assertEqual(r['planned'],2)
        self.assertIsNone(r['reported_cost_sum_usd'])
        self.assertEqual(r['ai']['end_to_end_correct_rate'],0)
    def test_field_accuracy_and_daily_cost(self):
        c={'expected_status':'PASS','ground_truth_fields':{'receipt_date':'2026-09-20','currency':'SGD','total':'12.50'}}
        prediction={'status':'PASS','fields':dict(c['ground_truth_fields'])}
        r=summarize([c],[{'regex':prediction,'ai':prediction,'log':{'usage':{'cost':.001}},'elapsed_seconds':1}])
        self.assertEqual(r['ai']['field_accuracy_including_nulls']['total'],1)
        self.assertEqual(r['daily_model_cost_at_80_receipts_usd'],.08)

if __name__=='__main__':unittest.main()
