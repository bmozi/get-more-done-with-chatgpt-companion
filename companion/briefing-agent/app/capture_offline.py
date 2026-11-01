"""Capture the real SDK loop using scripted responses. No live model is involved."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import socket
import subprocess
from pathlib import Path
from unittest.mock import patch
from core import CASES, BASE, SourceStore, reference_decision
from agent import run_case
from test_agent import ScriptedModel

async def capture():
    runs = {}
    for case_id in CASES:
        model = ScriptedModel(case_id)
        runs[case_id] = await run_case(case_id, model)
    return {'evidence_kind': 'real_sdk_loop_with_scripted_responses_not_model_reasoning',
            'live_provider_calls': False, 'network_and_child_process_guard': 'passed during capture',
            'python': platform.python_version(),
            'sdk_versions': {name: importlib.metadata.version(name) for name in ['openai-agents','openai','pydantic']},
            'runs': runs,
            'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'sources').glob('*.txt')}}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Refusing to overwrite earlier evidence')
    # Imports/package resolution occur before this guard, not during the capture.
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden')), patch.object(subprocess, 'Popen', side_effect=AssertionError('Child process forbidden')):
        report = asyncio.run(capture())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print('Captured four offline SDK cases; no provider called.')
