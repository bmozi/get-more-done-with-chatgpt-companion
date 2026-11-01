"""Local practice checks; no provider calls, network or user files."""
import re,json
from pathlib import Path
PATTERN = 'CL-[0-9]{3}'
def valid_identifier(value):return re.fullmatch(PATTERN,value) is not None
def within_limit(value,limit):return value<=limit
def inspect_cards(path):
    lines=Path(path).read_text(encoding='utf-8').splitlines();fronts=set()
    if not lines:raise ValueError('empty deck')
    for line in lines:
        fields=line.split('\t')
        if len(fields)!=2 or not all(x.strip() for x in fields):raise ValueError('exactly two nonempty fields required')
        if fields[0] in fronts:raise ValueError('duplicate question')
        fronts.add(fields[0])
    return len(lines)
if __name__=='__main__':
    print(json.dumps({'card_notes':inspect_cards(Path(__file__).with_name('flashcards.txt')),'kind':'local reference; no Anki or AI trial'}))
