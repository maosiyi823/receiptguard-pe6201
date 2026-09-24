import unittest
from receiptguard import assess, extract, evaluate

class CoreTests(unittest.TestCase):
    def run_case(self, amount='50.00', day='2026-08-25', currency='SGD'):
        return assess(extract(f'Date: {day}\n{currency}\nTotal: {amount}'), {'claim_category':'meal','submission_date':'2026-09-24'})
    def test_inclusive_boundaries(self):
        self.assertEqual(self.run_case()['status'],'PASS')
    def test_one_cent_over(self):
        self.assertEqual(self.run_case(amount='50.01')['status'],'FLAG')
    def test_one_day_late(self):
        self.assertEqual(self.run_case(day='2026-08-24')['status'],'FLAG')
    def test_future_date(self):
        self.assertEqual(self.run_case(day='2026-09-25')['status'],'FLAG')
    def test_bare_dollar_not_currency(self):
        self.assertEqual(self.run_case(currency='$')['status'],'ABSTAIN')
    def test_cash_not_total(self):
        self.assertEqual(extract('Total: 10.00\nCash: 20.00\nChange: 10.00')['fields']['total'],'10.00')
    def test_conflicting_total(self):
        self.assertIsNone(extract('Total: 10.00\nTotal: 20.00')['fields']['total'])
    def test_partial_violation_preserved(self):
        result=self.run_case(amount='80.00',currency='$')
        self.assertEqual(result['status'],'ABSTAIN')
        self.assertFalse(result['checks'][0]['pass'])
    def test_invalid_date(self):
        self.assertEqual(self.run_case(day='2026-02-30')['status'],'ABSTAIN')
    def test_abstain_does_not_earn_completion(self):
        cases=[{'expected_status':'ABSTAIN','ground_truth_fields':{}}]
        r=evaluate(cases,[{'status':'ABSTAIN','fields':{}}])
        self.assertEqual(r['end_to_end_correct_rate'],0)
        self.assertIsNone(r['answered_accuracy'])
        self.assertEqual(r['routing_accuracy'],1)
    def test_wrong_field_is_not_success(self):
        c={'expected_status':'PASS','ground_truth_fields':{'total':'10.00'}}
        r=evaluate([c],[{'status':'PASS','fields':{'total':'11.00'}}])
        self.assertEqual(r['end_to_end_correct_rate'],0)

if __name__=='__main__':
    unittest.main()
