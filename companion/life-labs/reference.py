"""Deterministic reference calculations for fictional book exercises; no AI calls."""
def classify(request, policy):
    fields=('people','meeting_start','meeting_minutes','public')
    if any(request.get(k) is None for k in fields):
        return 'incomplete'
    if not isinstance(request['public'],bool):
        raise ValueError('public must be boolean')
    if any(type(request[k]) is not int for k in fields[:3]):
        raise ValueError('headcount, start and duration must be integers')
    start=request['meeting_start']-policy['setup_minutes']
    end=request['meeting_start']+request['meeting_minutes']+policy['cleanup_minutes']
    if (request['people']<1 or request['people']>policy['capacity'] or request['meeting_minutes']<=0
        or start<policy['open_minute'] or end>policy['close_minute']
        or end-start>policy['maximum_reserved_minutes']):
        return 'ineligible'
    return 'review' if request['public'] and policy['public_event_requires_review'] else 'eligible'

def ledger(records, price):
    ids=set(); totals=dict(gross=0,refunds=0,net=0,earned=0,receivable=0,held=0)
    for row in records:
        if row['id'] in ids:raise ValueError('duplicate record ID')
        ids.add(row['id'])
        if row.get('status') not in ('delivered','booked_next_week','canceled_before_service'):
            raise ValueError('missing or unsupported status')
        cash=row['deposit_received']+row['balance_received']; refund=row['refund']; net=cash-refund
        if min(row['deposit_received'],row['balance_received'],refund)<0 or net<0 or net>price:
            raise ValueError('unsupported payment amount')
        earned=price if row['status']=='delivered' else 0
        if row['status']=='canceled_before_service' and net!=0:
            raise ValueError('canceled record must satisfy fictional full-refund policy')
        if row['status']=='delivered' and refund:
            raise ValueError('delivered refund requires a different policy')
        totals['gross']+=cash;totals['refunds']+=refund;totals['net']+=net
        totals['earned']+=earned
        totals['receivable']+=price-net if earned else 0
        totals['held']+=net if row['status']=='booked_next_week' else 0
    return totals
