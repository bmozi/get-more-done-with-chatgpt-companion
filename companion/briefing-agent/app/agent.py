"""OpenAI SDK candidate. Import does not call a provider. Live behavior unvalidated."""
import json
from agents import Agent, Runner, RunConfig, function_tool
from core import SourceStore, INSTRUCTIONS, validate_decision, render_brief


def build_agent(store, model):
    @function_tool(failure_error_function=None)
    def list_sources() -> str:
        """List source IDs and status available to this fictional case."""
        return json.dumps(store.catalog())

    @function_tool(failure_error_function=None)
    def read_source(source_id: str) -> str:
        """Read one allowed source ID. Filesystem paths are not accepted."""
        return json.dumps(store.read(source_id))

    return Agent(name='Fictional board briefing', instructions=INSTRUCTIONS,
                 model=model, tools=[list_sources, read_source])


async def run_case(case_id, model, store=None, max_turns=8):
    store = store or SourceStore(case_id)
    if store.case_id != case_id:
        raise ValueError('Store and requested case differ')
    result = await Runner.run(build_agent(store, model), json.dumps(store.case),
                              max_turns=max_turns, run_config=RunConfig(tracing_disabled=True))
    answer = validate_decision(store, json.loads(result.final_output))
    return {'answer': answer, 'brief': render_brief(store, answer), 'trace': store.trace,
            'model_requests': result.context_wrapper.usage.requests}


if __name__ == '__main__':
    import argparse
    import asyncio
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=__import__('core').CASES, default='standard')
    parser.add_argument('--model', required=True)
    parser.add_argument('--live', action='store_true', help='Required acknowledgement of a real provider run')
    args = parser.parse_args()
    if not args.live:
        parser.error('Use offline checks unless intentionally running a provider; --live is required')
    # This candidate uses normal SDK credential configuration. It never prints a key.
    # Turn/tool limits are not a dollar spending cap.
    print(json.dumps(asyncio.run(run_case(args.case, args.model)), indent=2))
