import copy
import unittest
from common_validation import validate_evidence

class GuardrailTests(unittest.TestCase):
    def sample(self, currency='SGD', total='18.00'):
        return {'fields':{'currency':currency,'total':total}, 'evidence':{'currency':currency,'total':total},'issues':[]}
    def test_bare_dollar_cannot_become_usd(self):
        original=self.sample('USD','10.00'); saved=copy.deepcopy(original)
        out=validate_evidence(original,'Total: $10.00')
        self.assertIsNone(out['fields']['currency'])
        self.assertEqual(out['raw_fields']['currency'],'USD')
        self.assertEqual(original,saved)
    def test_conflicting_totals_cleared(self):
        out=validate_evidence(self.sample(),'SGD\nTotal: 10.00\nTotal: 18.00')
        self.assertIsNone(out['fields']['total'])
        self.assertEqual(out['raw_fields']['total'],'18.00')
    def test_duplicate_equal_totals_ok(self):
        out=validate_evidence(self.sample(),'SGD\nTotal: 18.00\nTotal: 18.00')
        self.assertEqual(out['fields']['total'],'18.00')
    def test_subtotal_and_cash_not_conflicts(self):
        out=validate_evidence(self.sample(),'SGD\nSubtotal: 16.00\nTotal: 18.00\nCash: 20.00')
        self.assertEqual(out['fields']['total'],'18.00')
    def test_conflicting_currencies(self):
        out=validate_evidence(self.sample(),'SGD\nUSD\nTotal: 18.00')
        self.assertIsNone(out['fields']['currency'])

if __name__=='__main__':unittest.main()
