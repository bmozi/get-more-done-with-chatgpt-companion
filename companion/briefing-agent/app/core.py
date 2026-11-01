"""Closed fictional source exercise. No model, credentials, network or answer-key imports."""
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
import json
import re

BASE = Path(__file__).resolve().parents[1]
CASES = {c['id']: c for c in json.loads((BASE / 'cases.json').read_text())}

class ToolLimitError(RuntimeError):
    pass

@dataclass
class SourceStore:
    case_id: str
    max_calls: int = 8
    failed_ids: set = field(default_factory=set)
    trace: list = field(default_factory=list)
    read_ids: set = field(default_factory=set)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def __post_init__(self):
        self.case = CASES[self.case_id]
        # IDs come from the reviewed case file, never from a model-supplied path.
        self.sources = {}
        for sid in self.case['source_ids']:
            if not re.fullmatch(r'[A-Z0-9-]+', sid):
                raise ValueError('Invalid source ID in fixture')
            self.sources[sid] = (BASE / 'sources' / (sid + '.txt')).read_text()

    def _begin(self, tool, source_id=None):
        with self._lock:
            if len(self.trace) >= self.max_calls:
                raise ToolLimitError('Application tool-call limit reached')
            entry = {'tool': tool, 'source_id': source_id, 'completed': False}
            self.trace.append(entry)
            return entry

    def catalog(self):
        event = self._begin('list_sources')
        result = [{'source_id': sid, 'status': 'superseded' if 'Status: superseded' in text else 'current'}
                  for sid, text in self.sources.items()]
        with self._lock:
            event['completed'] = True
        return result

    def read(self, source_id):
        event = self._begin('read_source', source_id)
        if source_id not in self.sources:
            raise ValueError('Source ID is not available in this case')
        if source_id in self.failed_ids:
            raise TimeoutError('Injected local source-read failure')
        with self._lock:
            self.read_ids.add(source_id)
            event['completed'] = True
        return {'source_id': source_id, 'text': self.sources[source_id]}


def quoted_amounts(text):
    """Read exactly this fixture's three quote fields; not a general document parser."""
    patterns = [r'scanner: \$(\d+)', r'Delivery: \$(\d+)',
                r'(?:mandatory photo carrier kit|Required desktop software licence): \$(\d+)']
    amounts = []
    for pattern in patterns:
        match = re.search(pattern, text)
        if match is None:
            raise ValueError('Unsupported quotation format')
        amounts.append(int(match.group(1)))
    return amounts


def reference_decision(store):
    """Deterministic exercise baseline. Does not simulate model reasoning or tool use."""
    costs = []
    for sid in ('A-CURRENT', 'B-CURRENT'):
        if sid in store.sources:
            amounts = quoted_amounts(store.sources[sid])
            costs.append({'source_id': sid, 'amounts': amounts, 'total': sum(amounts)})
    affordable = [c for c in costs if c['total'] <= store.case['budget']]
    if store.case['requires_film']:
        status, option = 'insufficient_capability_evidence', None
    elif affordable:
        status, option = 'supported_option', min(affordable, key=lambda c: c['total'])['source_id']
    elif 'A-CURRENT' not in store.sources:
        status, option = 'no_supported_recommendation', None
    else:
        status, option = 'no_affordable_supported_option', None
    unanswered = ['warranty_terms', 'representative_demand']
    if store.case['requires_film']:
        unanswered.append('film_capability')
    if 'A-CURRENT' not in store.sources:
        unanswered.append('current_alder_quote')
    return {'status': status, 'option': option, 'costs': costs,
            'unanswered': unanswered, 'demand_proven': False,
            'citations': sorted(store.sources)}


def validate_decision(store, answer):
    # JSON shape alone does not establish truth. This narrow exercise also checks
    # meaning against its fixture facts. New document formats need new review.
    expected = reference_decision(store)
    if not isinstance(answer, dict) or set(answer) != set(expected):
        raise ValueError('Expected only the declared decision fields; no action fields')
    if store.read_ids != set(store.sources):
        raise ValueError('All available case sources must be read before accepting the brief')
    costs = answer.get('costs')
    if not isinstance(costs, list) or any(not isinstance(c, dict) or set(c) != {'source_id', 'amounts', 'total'} for c in costs):
        raise ValueError('Invalid cost record structure')
    for cost in costs:
        if not isinstance(cost['amounts'], list) or any(type(n) is not int for n in cost['amounts']) or type(cost['total']) is not int:
            raise ValueError('Cost fields must contain integer dollars, not strings or booleans')
    if answer['demand_proven'] is not False:
        raise ValueError('The packet does not establish representative demand')
    if not isinstance(answer['citations'], list) or not all(isinstance(s, str) for s in answer['citations']):
        raise ValueError('Citations must be source IDs')
    if set(answer['citations']) != store.read_ids or len(set(answer['citations'])) != len(answer['citations']):
        raise ValueError('Citations must match the actual source reads exactly')
    # Cost/question/citation order is not educationally meaningful.
    normalized = dict(answer)
    normalized['costs'] = sorted(costs, key=lambda c: c['source_id'])
    for key in ('unanswered', 'citations'):
        if not isinstance(answer[key], list) or not all(isinstance(s, str) for s in answer[key]):
            raise ValueError('Expected string lists')
        normalized[key] = sorted(answer[key])
    expected['costs'] = sorted(expected['costs'], key=lambda c: c['source_id'])
    expected['unanswered'] = sorted(expected['unanswered'])
    if normalized != expected:
        raise ValueError('Brief disagrees with current costs, requirements or evidence limits')
    return normalized


def render_brief(store, answer):
    """Render checked fields. No unchecked model prose is promoted to a factual claim."""
    answer = validate_decision(store, answer)
    lines = ['Maple Digital Archive — fictional board brief',
             'Decision: ' + answer['status'].replace('_', ' '),
             'Option: ' + (answer['option'] or 'No supported selection'),
             f"Budget cap: ${store.case['budget']} (case update governs)"]
    for cost in answer['costs']:
        lines.append(f"{cost['source_id']}: " + ' + '.join('$' + str(n) for n in cost['amounts']) + f" = ${cost['total']}")
    lines.extend(['Both available current quotations state support for loose photographic prints.' if len(answer['costs']) == 2 else 'The available current quotation states support for loose photographic prints.',
                  'A-OLD is superseded and is not evidence of current price.',
                  'The interest note does not establish representative demand or willingness to pay.',
                  'Questions: ' + ', '.join(answer['unanswered']).replace('_', ' '),
                  'Sources read: ' + ', '.join(answer['citations']),
                  'Draft only. No order placed or vendor contacted.'])
    return '\n'.join(lines)


INSTRUCTIONS = '''You prepare a structured decision for a FICTIONAL board briefing.
Use list_sources, then read every available source. Only use those sources.
The task's budget and film requirement override conflicting BRIEF-01 requirements.
Use current quotes, include delivery and mandatory extras, and do not infer film
support or warranty terms. Five informal positive replies are not proven demand.
Return JSON only with exactly: status, option, costs, unanswered, demand_proven,
citations. costs is a list of {source_id, amounts, total}; amounts contains the
scanner, delivery and mandatory extra in that order, all integer dollars.
status is supported_option, no_affordable_supported_option,
insufficient_capability_evidence, or no_supported_recommendation. option is a
current quote source ID or null. If required film support is unspecified, use
insufficient_capability_evidence. Without A-CURRENT and with the remaining quote
unaffordable, use no_supported_recommendation. unanswered contains warranty_terms
and representative_demand; add film_capability when film is required and
current_alder_quote if A-CURRENT is unavailable. demand_proven must be false.
Citations must include each source ID actually read, including superseded history.
Never contact a vendor, place an order, or claim that an action happened.'''

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, default='standard')
    args = parser.parse_args()
    store = SourceStore(args.case)
    print(json.dumps({'evidence_kind': 'deterministic_fixture_baseline_not_agent',
                      'answer': reference_decision(store)}, indent=2))
