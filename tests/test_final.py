import unittest
from run_final import report

class FinalTests(unittest.TestCase):
    def fixture(self):
        c={'group':'clean','source_type':'synthetic','expected_status':'PASS','ground_truth_fields':{'total':'10.00','currency':'SGD','receipt_date':'2026-09-20'},'expected_checks':{'meal_limit':True,'submission_window':True}}
        p={'status':'PASS','fields':dict(c['ground_truth_fields']),'checks':[{'rule':'meal_limit','pass':True},{'rule':'submission_window','pass':True}]}
        r={'regex':p,'ai':p,'log':{'usage':{'cost':.001}},'regex_seconds':.001,'ai_seconds':1}
        return c,r
    def test_partial_has_no_headline(self):
        c,r=self.fixture();out=report([c,c],[r])
        self.assertIsNone(out['headline_metrics']);self.assertFalse(out['complete'])
        self.assertIn('partial_metrics_not_final',out)
    def test_complete_and_group_metrics(self):
        c,r=self.fixture();out=report([c],[r])
        self.assertEqual(out['headline_metrics']['ai']['correct_automated_count'],1)
        self.assertEqual(out['groups']['group']['clean']['n'],1)
        self.assertEqual(out['headline_metrics']['ai']['rule_accuracy_evaluable_only']['meal_limit']['correct'],1)
    def test_majority_fixed_not_test_selected(self):
        c,r=self.fixture();c['expected_status']='FLAG'
        self.assertEqual(report([c],[r])['fixed_development_majority_reference']['label'],'PASS')
    def test_missing_cost_unknown(self):
        c,r=self.fixture();r['log']={}
        self.assertIsNone(report([c],[r])['cost']['mean_usd'])
if __name__=='__main__':unittest.main()
