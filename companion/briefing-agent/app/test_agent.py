"""Failure/observation tests with scripted responses; no live model reasoning."""
import concurrent.futures
import copy
import json
import unittest
from pathlib import Path
from core import SourceStore, ToolLimitError, CASES, reference_decision, validate_decision, render_brief
from agent import run_case, build_agent
from agents import Model, ModelResponse
from agents.exceptions import MaxTurnsExceeded, UserError
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText


def read_all(store):
    for source in store.catalog():
        store.read(source['source_id'])
    return store


class FixtureTests(unittest.TestCase):
    def test_four_reference_cases_match_separate_reviewer_key(self):
        keys = json.loads((Path(__file__).parents[1] / 'reviewer/expected.json').read_text())['cases']
        for case_id in CASES:
            with self.subTest(case=case_id):
                store = read_all(SourceStore(case_id))
                actual = validate_decision(store, reference_decision(store))
                self.assertEqual(actual['status'], keys[case_id]['status'])
                self.assertEqual(actual['option'], keys[case_id]['option'])
                self.assertEqual({c['source_id']: c['total'] for c in actual['costs']}, keys[case_id]['checked_totals'])
                self.assertIn('Draft only', render_brief(store, actual))

    def test_omitted_mandatory_cost_rejected(self):
        store = read_all(SourceStore('standard')); answer = reference_decision(store)
        answer['costs'][1].update(amounts=[299,19], total=318)
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            validate_decision(store, answer)

    def test_affordable_price_cannot_override_missing_film_evidence(self):
        store = read_all(SourceStore('film-required')); answer = reference_decision(store)
        answer.update(status='supported_option', option='A-CURRENT')
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            validate_decision(store, answer)

    def test_old_quote_cannot_replace_unavailable_current_quote(self):
        store = read_all(SourceStore('missing-current-a')); answer = reference_decision(store)
        answer.update(status='supported_option', option='A-OLD')
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            validate_decision(store, answer)
        with self.assertRaises(ValueError):
            store.read('A-CURRENT')

    def test_unread_sources_prevent_acceptance(self):
        store = SourceStore('standard');store.read('A-CURRENT')
        with self.assertRaisesRegex(ValueError, 'must be read'):
            validate_decision(store, reference_decision(store))

    def test_demand_overclaim_rejected(self):
        store = read_all(SourceStore('standard')); answer = reference_decision(store);answer['demand_proven'] = True
        with self.assertRaisesRegex(ValueError, 'demand'):
            validate_decision(store, answer)

    def test_actions_and_fabricated_citations_rejected(self):
        store = read_all(SourceStore('standard')); answer = reference_decision(store)
        action = copy.deepcopy(answer);action['order_placed'] = True
        with self.assertRaisesRegex(ValueError, 'fields'):
            validate_decision(store, action)
        answer['citations'].append('WARRANTY-UNSEEN')
        with self.assertRaisesRegex(ValueError, 'Citations'):
            validate_decision(store, answer)

    def test_boolean_dollars_rejected_even_when_equal_to_int(self):
        store = read_all(SourceStore('standard')); answer = reference_decision(store)
        answer['costs'][0]['amounts'][0] = True
        with self.assertRaisesRegex(ValueError, 'integer'):
            validate_decision(store, answer)

    def test_arbitrary_path_rejected_and_recorded_incomplete(self):
        store = SourceStore('standard')
        with self.assertRaises(ValueError):
            store.read('../reviewer/expected.json')
        self.assertFalse(store.trace[-1]['completed'])

    def test_read_failure_is_not_a_completed_observation(self):
        store = SourceStore('standard', failed_ids={'A-CURRENT'})
        with self.assertRaises(TimeoutError):
            store.read('A-CURRENT')
        self.assertNotIn('A-CURRENT', store.read_ids)
        self.assertFalse(store.trace[-1]['completed'])

    def test_parallel_tool_calls_cannot_exceed_shared_limit(self):
        store = SourceStore('standard', max_calls=1)
        def attempt(_):
            try:
                store.catalog();return True
            except ToolLimitError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt, range(24))), 1)
        self.assertEqual(len(store.trace), 1)


class ScriptedModel(Model):
    def __init__(self, case_id, *, loop=False, bad_cost=False):
        self.case_id, self.loop, self.bad_cost = case_id, loop, bad_cost
        self.calls = 0

    async def get_response(self, system_instructions, input, *args, **kwargs):
        self.calls += 1
        if self.calls == 1 or self.loop:
            output = [ResponseFunctionToolCall(arguments='{}', call_id=f'catalog_{self.calls}', name='list_sources', type='function_call')]
        elif self.calls == 2:
            if 'A-OLD' not in json.dumps(input):
                raise AssertionError('Catalog observation missing from SDK history')
            output = [ResponseFunctionToolCall(arguments=json.dumps({'source_id': sid}), call_id='read_'+sid,
                       name='read_source', type='function_call') for sid in CASES[self.case_id]['source_ids']]
        else:
            history = json.dumps(input)
            if 'not a representative demand study' not in history:
                raise AssertionError('Source-read observations missing from SDK history')
            # This is an explicit fixed reference, not a reasoning model.
            answer = reference_decision(SourceStore(self.case_id))
            if self.bad_cost:
                answer['costs'][0]['total'] = 1
            output = [ResponseOutputMessage(id='fixture_final', content=[ResponseOutputText(annotations=[], text=json.dumps(answer), type='output_text')], role='assistant', status='completed', type='message')]
        return ModelResponse(output=output, usage=Usage(requests=1), response_id=f'fixture_{self.calls}')

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError
        yield


class SDKTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_loop_carries_parallel_source_observations_for_all_cases(self):
        for case_id in CASES:
            with self.subTest(case=case_id):
                model = ScriptedModel(case_id)
                result = await run_case(case_id, model)
                self.assertEqual(model.calls, 3)
                self.assertEqual(result['model_requests'], 3)
                self.assertEqual(len(result['trace']), 1+len(CASES[case_id]['source_ids']))
                self.assertTrue(all(t['completed'] for t in result['trace']))

    async def test_valid_json_with_wrong_cost_fails_after_sdk(self):
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            await run_case('standard', ScriptedModel('standard', bad_cost=True))

    async def test_repeating_model_stopped_by_turn_limit(self):
        with self.assertRaises(MaxTurnsExceeded):
            await run_case('standard', ScriptedModel('standard', loop=True), max_turns=2)

    async def test_tool_limit_survives_sdk_wrapper(self):
        with self.assertRaises(UserError) as caught:
            await run_case('standard', ScriptedModel('standard', loop=True), SourceStore('standard', max_calls=1))
        self.assertIsInstance(caught.exception.__cause__, ToolLimitError)

    async def test_source_failure_aborts_instead_of_fabricating_a_brief(self):
        store = SourceStore('standard', failed_ids={'A-CURRENT'})
        with self.assertRaises(UserError) as caught:
            await run_case('standard', ScriptedModel('standard'), store)
        self.assertIsInstance(caught.exception.__cause__, TimeoutError)

    async def test_only_source_tools_exposed(self):
        self.assertEqual({t.name for t in build_agent(SourceStore('standard'), ScriptedModel('standard')).tools},
                         {'list_sources','read_source'})


if __name__ == '__main__':
    unittest.main()
