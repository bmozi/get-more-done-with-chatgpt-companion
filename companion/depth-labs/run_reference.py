"""Print actual local reference outcomes; no provider or external actions."""
import json
from pathlib import Path
from reference import room, LocalDestination, recover
base=Path(__file__).resolve().parent
cases=json.loads((base/'room-requests.json').read_text())
results={'kind':'actual deterministic local run; no live model evidence','room':{r['id']:room(r) for r in cases},'recovery':{}}
for scenario in ['before-action','lost-acknowledgment','unavailable']:
    dest=LocalDestination();log=dict(operation='OP-A-D3',content='D3',approved_content='D3',state='attempted')
    if scenario=='lost-acknowledgment':dest.accept('OP-A-D3','D3')
    if scenario=='unavailable':dest.available=False
    results['recovery'][scenario]={'result':recover(log,dest),'destination_records':len(dest.records)}
print(json.dumps(results,indent=2))
