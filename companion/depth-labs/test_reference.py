import unittest
from copy import deepcopy
from reference import room, minute, LocalDestination, recover, gate, digest, ledger

class RoomChecks(unittest.TestCase):
    def request(self, **changes):
        return dict(people=6, start='10:00', duration=60, public=False, **{}) | changes
    def test_exact_boundaries(self):
        for start,duration,interval in [('09:15',30,'09:00–10:00'),('16:15',90,'16:00–18:00')]:
            result=room(self.request(start=start,duration=duration));self.assertEqual((result['classification'],result['interval']),('eligible',interval))
    def test_one_minute_failures(self):
        for start,duration,reason in [('09:14',30,'opening'),('16:16',90,'closing'),('10:00',91,'reserved duration')]:
            result=room(self.request(start=start,duration=duration));self.assertIn(reason,result['failures']);self.assertEqual(result['classification'],'ineligible')
    def test_priority(self):
        self.assertEqual(room(self.request(people=9,public=True))['classification'],'ineligible')
        self.assertEqual(room(self.request(public=True))['classification'],'staff review')
    def test_missing_precedes_known_failure(self):
        r=self.request(start='17:00');del r['people'];result=room(r);self.assertEqual(result['classification'],'incomplete');self.assertEqual(result['interval'],'16:45–18:15');self.assertIn('closing',result['known_concerns'])
    def test_changed_closing_preserves_duration(self):
        self.assertEqual(room(self.request(start='16:16',duration=90),closing='18:30')['classification'],'eligible')
        self.assertEqual(room(self.request(duration=91),closing='18:30')['classification'],'ineligible')
    def test_interval_crosses_midnight(self):
        result=room(self.request(start='00:00',duration=30));self.assertEqual(result['interval'],'day -1 23:45–00:45');self.assertIn('opening',result['failures'])
    def test_bad_inputs(self):
        for changes in [dict(start='25:00'),dict(start='9:00'),dict(duration=-1),dict(people=True),dict(public='private')]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):room(self.request(**changes))

class RecoveryChecks(unittest.TestCase):
    def setUp(self):self.d=LocalDestination();self.log=dict(operation='OP-A-D3',content='D3',approved_content='D3',state='attempted')
    def test_before_action(self):
        out=recover(self.log,self.d);self.assertEqual(out['state'],'confirmed');self.assertEqual(len(self.d.records),1)
    def test_lost_acknowledgment_no_duplicate(self):
        receipt=self.d.accept('OP-A-D3','D3');out=recover(self.log,self.d);self.assertEqual(out['receipt'],receipt);self.assertEqual(len(self.d.records),1)
    def test_destination_deduplicates_same_identity(self):
        self.assertEqual(self.d.accept('x','D3'),self.d.accept('x','D3'));self.assertEqual(len(self.d.records),1)
    def test_changed_content_rejected(self):
        self.d.accept('x','D3')
        with self.assertRaises(ValueError):self.d.accept('x','D4')
    def test_unknown_holds(self):
        self.d.available=False;self.assertEqual(recover(self.log,self.d)['state'],'unresolved');self.assertFalse(self.d.records)
    def test_new_content_needs_review(self):
        self.log['content']='D4';self.assertEqual(recover(self.log,self.d)['state'],'review required');self.assertFalse(self.d.records)
    def test_identity_content_conflict(self):
        self.d.accept('OP-A-D3','OTHER');self.assertEqual(recover(self.log,self.d)['state'],'conflict')
    def test_new_identity_can_duplicate(self):
        self.d.accept('first','D3');self.d.accept('second','D3');self.assertEqual(len(self.d.records),2)

class GateChecks(unittest.TestCase):
    def setUp(self):
        self.p=dict(classification='eligible',action='draft',request='Q1',policy='R1',destination='private-draft',content='Eligible under R1')
        self.r={k:self.p[k] for k in ['request','policy','destination']};self.r['content_sha256']=digest(self.p['content'])
    def test_clean_control(self):self.assertTrue(gate(self.p,self.r)[0])
    def test_action_destination_label_separately(self):
        for key,value in [('action','send'),('destination','external-review@example.invalid'),('classification','approved'),('classification',[])]:
            p=self.p|{key:value};self.assertFalse(gate(p,self.r)[0])
    def test_stale_policy_wrong_request(self):
        for key,value in [('policy','R0'),('request','Q2')]:self.assertFalse(gate(self.p|{key:value},self.r)[0])
    def test_unexpected_disclosure_field(self):self.assertFalse(gate(self.p|{'other_request_contact':'fictional'},self.r)[0])
    def test_changed_content(self):self.assertFalse(gate(self.p|{'content':'Edited after review'},self.r)[0])
    def test_hash_is_not_truth(self):
        p=self.p|{'content':'An unsupported claim'};r=self.r|{'content_sha256':digest(p['content'])};self.assertTrue(gate(p,r)[0])

class LedgerChecks(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(id='R1',status='delivered',deposit=20,balance=40,refund=0),dict(id='R2',status='delivered',deposit=20,balance=0,refund=0),dict(id='R3',status='booked',deposit=20,balance=0,refund=0),dict(id='R4',status='canceled',deposit=20,balance=0,refund=20)]
    def test_base(self):
        t=ledger(self.rows);self.assertEqual([t[k] for k in ['gross','net_cash','earned','unpaid','future_deposits']],[120,100,120,40,20]);self.assertTrue(t['reconciles'])
    def test_payment_not_delivery(self):
        self.rows[1]['balance']=40;t=ledger(self.rows);self.assertEqual((t['net_cash'],t['earned'],t['unpaid']),(140,120,0))
    def test_duplicate_missing_status(self):
        with self.assertRaises(ValueError):ledger(self.rows+[self.rows[0]])
        del self.rows[0]['status']
        with self.assertRaises(ValueError):ledger(self.rows)
    def test_wrong_status_still_balances(self):
        self.rows[2]['status']='delivered';t=ledger(self.rows);self.assertTrue(t['reconciles']);self.assertEqual((t['earned'],t['unpaid']),(180,80))
    def test_unpaid_booking_then_delivery(self):
        self.rows.append(dict(id='R5',status='booked',deposit=0,balance=0,refund=0));self.assertEqual(ledger(self.rows)['net_cash'],100)
        self.rows[-1]['status']='delivered';t=ledger(self.rows);self.assertEqual((t['earned'],t['unpaid']),(180,100))
    def test_outside_terms_rejected(self):
        self.rows[0]['refund']=2
        with self.assertRaises(ValueError):ledger(self.rows)

if __name__=='__main__':unittest.main()
