"""Hand-designed deterministic development fixtures. No random/model generation."""
import json
from pathlib import Path

cases = []
def add(name, text, fields, status, note, category='meal', submitted='2026-09-24'):
    cases.append(dict(case_id=name, source_type='synthetic_development', receipt_text=text, claim_metadata=dict(claim_category=category, submission_date=submitted), ground_truth_fields=dict(zip(('receipt_date','currency','total'), fields)), expected_status=status, annotation_note=note))

base = 'Merchant: Demo Cafe\nDate: 2026-09-20\nCurrency: SGD\nTotal: '
add('dev01',base+'12.50',('2026-09-20','SGD','12.50'),'PASS','普通合规开发例')
add('dev02',base+'50.00',('2026-09-20','SGD','50.00'),'PASS','金额上限包含等于')
add('dev03',base+'50.01',('2026-09-20','SGD','50.01'),'FLAG','超限一分')
add('dev04','Date: 2026-08-25\nSGD\nTotal: 10.00',('2026-08-25','SGD','10.00'),'PASS','恰好30天')
add('dev05','Date: 2026-08-24\nSGD\nTotal: 10.00',('2026-08-24','SGD','10.00'),'FLAG','31天')
add('dev06','Date: 2026-09-25\nSGD\nTotal: 10.00',('2026-09-25','SGD','10.00'),'FLAG','未来日期')
add('dev07','Date: 2026-09-20\nTotal: $10.00',('2026-09-20',None,'10.00'),'ABSTAIN','美元符号不足以判断币种')
add('dev08','Date: 2026-09-20\nSGD\nTotal: 10.00\nTotal: 18.00',('2026-09-20','SGD',None),'ABSTAIN','总额冲突')
add('dev09','Date: 2026-09-20\nUSD\nTotal: 10.00',('2026-09-20','USD','10.00'),'ABSTAIN','范围不支持USD，不是违规')
add('dev10','SGD\nTotal: 10.00',(None,'SGD','10.00'),'ABSTAIN','缺日期')
add('dev11','Date: 2026-09-20\nSGD\nSubtotal: 10.00\nTax: 0.90\nTotal: 10.90\nCash: 20.00\nChange: 9.10',('2026-09-20','SGD','10.90'),'PASS','多个金额，勿把现金当总额')
add('dev12','Date: 2026-09-20\nSGD\nT0TAL: 12.50',('2026-09-20','SGD','12.50'),'PASS','关键词字符噪声，金额仍可人工判断')
add('dev13','Date: 2026-09-20\nSGD\nGrand total\n12.50',('2026-09-20','SGD','12.50'),'PASS','跨行总额，检验空白处理')
add('dev14',base+'12.50',('2026-09-20','SGD','12.50'),'ABSTAIN','不支持的费用类别',category='hotel')
Path(__file__).with_name('dev.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
