# Depth labs — local references and independent practice

Begin with WORKBOOK.md and the corresponding book chapter. All packets are fictional. The scanner mini packet in Chapter 7 is intentionally separate from the original briefing-agent application. Its totals should not replace that application's source records.

From this directory, using Python 3.10 or later:

```sh
python3 run_reference.py
python3 -m unittest -v test_reference.py
```

The first command prints deterministic room decisions and local recovery outcomes. It creates no schedule, makes no model call and sends no message. The second checks policy boundaries/priority, modeled recovery, draft gates and ledger definitions. No additional packages are required. These small programs are teaching references, not production integrations.

- packets/: inputs for the worked lessons.
- prompt-scorecard.csv: blank observed-output fields, marked not run.
- chain-faults.md and specialist-findings.csv: intentionally authored faulty outputs.
- reviewer/answer-key.json: inspect after your own attempt.
- reference.py: inspectable calculations and boundaries.

For live ChatGPT trials, save the exact packet, prompt, configuration and actual response in your own attempt folder. Do not put private records or credentials in a shared practice repository. A local passing test does not establish live model reliability or reader learning. Existing original SDK application tests remain in ../briefing-agent/ and are a separate evidence set.
