"""Small, inspectable fictional references. No model calls or network access."""
from copy import deepcopy
from hashlib import sha256
import re

REQUIRED = ('people', 'start', 'duration', 'public')

def minute(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', value):
        raise ValueError('start must be a valid 24-hour HH:MM time')
    hour, minutes = map(int, value.split(':'))
    return hour * 60 + minutes


def clock(value):
    days, within = divmod(value, 24 * 60)
    label = f'{within // 60:02}:{within % 60:02}'
    return label if days == 0 else f'day {days:+d} {label}'


def room(request, closing='18:00'):
    missing = [key for key in REQUIRED if key not in request or request[key] is None]
    # The teaching policy explicitly prioritizes missing required fields.
    if missing:
        interval = None; concerns = []
        if type(request.get('people')) is int and request['people'] > 8: concerns.append('capacity')
        if request.get('start') is not None and type(request.get('duration')) is int and request['duration'] > 0:
            start = minute(request['start']); begin = start - 15; end = start + request['duration'] + 15
            interval = f'{clock(begin)}–{clock(end)}'
            if begin < 9 * 60: concerns.append('opening')
            if end > minute(closing): concerns.append('closing')
            if request['duration'] + 30 > 120: concerns.append('reserved duration')
        return {'classification': 'incomplete', 'missing': missing, 'interval': interval, 'known_concerns': concerns}
    people, duration = request['people'], request['duration']
    if type(people) is not int or people < 1 or type(duration) is not int or duration < 1:
        raise ValueError('people and duration must be positive integers')
    if type(request['public']) is not bool:
        raise ValueError('public must be true or false')
    start = minute(request['start']); begin = start - 15; end = start + duration + 15
    interval = f'{clock(begin)}–{clock(end)}'
    failures = []
    if people > 8: failures.append('capacity')
    if begin < 9 * 60: failures.append('opening')
    if end > minute(closing): failures.append('closing')
    if duration + 30 > 120: failures.append('reserved duration')
    return {'classification': 'ineligible' if failures else ('staff review' if request['public'] else 'eligible'),
            'interval': interval, 'missing': [], 'failures': failures, 'reserved_minutes': duration + 30}


class LocalDestination:
    """A modeled destination, not a publishing client."""
    def __init__(self):
        self.records = {}
        self.available = True

    def accept(self, operation, content):
        if not self.available: raise ConnectionError('destination unavailable')
        if operation in self.records:
            if self.records[operation]['content'] != content:
                raise ValueError('operation identity reused with different content')
            return self.records[operation]['receipt']
        receipt = f'LOCAL-{len(self.records) + 1}'
        self.records[operation] = {'content': content, 'receipt': receipt}
        return receipt

    def inspect(self, operation):
        if not self.available: raise ConnectionError('destination unavailable')
        return self.records.get(operation)


def recover(log, destination):
    """Resume only a modeled publication whose artifact identity is unchanged."""
    result = deepcopy(log)
    try:
        found = destination.inspect(log['operation'])
    except ConnectionError:
        result.update(state='unresolved', next_action='owner review; no automatic retry')
        return result
    if found and found['content'] != log['content']:
        result.update(state='conflict', next_action='review content/operation mismatch')
        return result
    if found:
        result.update(state='confirmed', receipt=found['receipt'], recovery='existing receipt')
        return result
    if log.get('approved_content') != log['content']:
        result.update(state='review required', next_action='review changed content')
        return result
    receipt = destination.accept(log['operation'], log['content'])
    result.update(state='confirmed', receipt=receipt, recovery='one permitted local action')
    return result


def digest(text):
    return sha256(text.encode('utf-8')).hexdigest()


def gate(proposal, review):
    """Validate this closed draft-export format. Does not send or publish."""
    expected = {'action', 'request', 'policy', 'destination', 'content', 'classification'}
    if not isinstance(proposal, dict) or set(proposal) != expected: return False, 'missing or unexpected fields'
    if proposal['action'] != 'draft': return False, 'operation not allowed'
    if not isinstance(proposal['classification'], str) or proposal['classification'] not in {'incomplete', 'ineligible', 'staff review', 'eligible'}: return False, 'classification not allowed'
    for field in ('request', 'policy', 'destination'):
        if proposal[field] != review[field]: return False, field + ' mismatch'
    if not isinstance(proposal['content'], str): return False, 'content must be text'
    if digest(proposal['content']) != review['content_sha256']: return False, 'changed content requires review'
    return True, 'accepted local draft only'


def ledger(rows):
    """Teaching definitions only; not an accounting system."""
    seen = set(); totals = dict(gross=0, refunds=0, net_cash=0, earned=0, unpaid=0, future_deposits=0, future_bookings=0)
    for row in rows:
        if row['id'] in seen: raise ValueError('duplicate identity')
        seen.add(row['id']); status = row.get('status')
        if status not in {'delivered', 'booked', 'canceled'}: raise ValueError('unsupported or missing status')
        dep, bal, refund = [row[k] for k in ('deposit', 'balance', 'refund')]
        if any(type(v) is not int or v < 0 for v in [dep, bal, refund]): raise ValueError('amounts must be nonnegative integer dollars')
        if dep + bal > 60 or refund > dep + bal: raise ValueError('unsupported payment amounts')
        if status == 'canceled' and dep + bal != refund: raise ValueError('exercise requires full cancellation refund')
        if status != 'canceled' and refund: raise ValueError('refund scenario outside exercise')
        totals['gross'] += dep + bal; totals['refunds'] += refund
        if status == 'delivered': totals['earned'] += 60; totals['unpaid'] += 60 - dep - bal
        if status == 'booked':
            if bal: raise ValueError('exercise collects booking deposit only')
            totals['future_deposits'] += dep; totals['future_bookings'] += 1
    totals['net_cash'] = totals['gross'] - totals['refunds']
    totals['reconciles'] = totals['net_cash'] + totals['unpaid'] == totals['earned'] + totals['future_deposits']
    return totals
