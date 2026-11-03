# Build toward a checked briefing

This is an original fictional source packet and candidate SDK implementation for proposed units U33–U34. It has 17 passing offline tests; live model behavior remains untested. The lesson design (private development record; not included in this download) explains the different educational purpose alongside Claude's operations/manual agent.

The household of the Maple family needs a short decision brief about a laptop. The packet contains a superseded quote, two current quotes with mandatory extras, and a small informal interest note. The reader must explain which recommendation is supported, calculate complete quoted costs, and preserve what remains unknown.

## Start with a manual baseline

Read the source files listed in one case in [cases.json](cases.json). The case's update overrides the corresponding requirement in BRIEF-01. Do not supply a source that the case marks unavailable. Write your own brief before consulting the reviewer key.

Use this request for a future text-conversation pilot:

> Prepare a brief for the Maple family using only the supplied fictional sources and the case update. Lead with a supported option, no affordable supported option, or insufficient evidence. Include total quoted costs with mandatory extras, source IDs for claims, and questions the sources leave unanswered. Treat superseded quotes as historical. Distinguish an informal interest note from evidence of regular use. Draft only; do not contact vendors or place an order.

Do not call the text-conversation pilot an agent-application test. It supplies a simpler baseline for deciding whether tool use adds value.

## Acceptance before construction

After trying each case, compare with the private [acceptance key](reviewer/expected.json) and [cost ledger](reviewer/cost-ledger.json). These files are for the evaluator, not inputs to the model. Cases are development fixtures; because they are documented here, they are not held-out research data. Create new private cases before measuring generalization.

In the standard case, the household should be able to see the full cost calculation, the reason for using the current quote, and what the packet cannot establish. A readable paragraph with the wrong accessory cost fails. A correct number followed by an invented warranty also fails.

The candidate developer implementation will need a source catalog and a source-reading tool with an allowlist. Only IDs in the active case may be read. Tool responses should carry source IDs and status; missing or failed reads must remain visible. The checked structured result should contain decision status, option, calculations, supported claims, unanswered questions and citations. Retain the actual tool trace and verify that cited sources were read.

No purchase or messaging tool is needed for this job. Set explicit turn/tool limits, record actual usage, and compare the result with the manual and text-conversation baselines. Configure any supported cost controls explicitly rather than assuming a turn limit is a dollar cap.

## Evidence still needed

The local checker verifies fixture arithmetic, references and consistency. It does not run a model, validate an agent, score the quality of prose, or observe reader learning. The OpenAI SDK wiring evidence in the inherited Claude-origin lab used scripted responses and a different source packet; it does not validate this project.

Before presenting a completed agent lesson, implement the provider-specific runner, inspect actual calls and results, test failure and recovery, and ask readers to explain a changed decision unaided. Record product/account configuration without guessing hidden model identity. Keep any repeatability or purchase-interest claim tied to evidence actually obtained.

## Run the local implementation

The [application](app/core.py) supplies a closed source registry, a deterministic reference, source-read traces and a checked decision contract. [The SDK adapter](app/agent.py) exposes only source catalog/read tools. It renders a short purchase brief from accepted structured fields; it does not treat arbitrary generated prose as verified evidence. The fixed quotation reader understands this fictional packet only. It is not a general procurement or document-understanding system.

From the repository root:

```sh
python3 companion/briefing-agent/app/core.py --case standard
uv run --with openai-agents==0.24.0 python -m unittest discover -s companion/briefing-agent/app -p 'test_agent.py' -v
```

The first command is a deterministic baseline, not an agent. The second runs the real SDK loop with scripted responses and checks actual tool callbacks and observations. It covers all four cases, wrong costs, missing capability evidence, stale quotes, unread sources, regular-use overclaims, extra action fields, invalid dollars, arbitrary paths, failed reads, concurrent limits and stopping. The captured test run blocked socket connections and child processes during execution; package resolution and imports occurred before that guard. Captured evidence (private development record; not included in this download).

For an intentional future live trial with an explicitly chosen model and normal SDK account configuration:

```sh
uv run --with openai-agents==0.24.0 python companion/briefing-agent/app/agent.py --live --model YOUR_CHOSEN_MODEL --case standard
```

That command is an unrun candidate. The `--live` flag prevents accidental CLI execution without an explicit acknowledgement. The application limits tools to eight calls and the runner to eight model turns; neither is a dollar spending cap. No provider credentials were accessed or provider calls made in this milestone.

The application uses a narrow fixture-specific semantic checker as well as JSON parsing. That gives this teaching case clear acceptance criteria. It does not establish general reasoning quality, trustworthy citations on new corpora or usability for readers. Keep the four visible cases as development cases, then create separate unseen sources and decisions for broader evaluation.
