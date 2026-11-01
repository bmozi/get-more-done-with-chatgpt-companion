# Practical fluency references

Begin with [the workbook](WORKBOOK.md) and its corresponding book chapters. This directory contains original fictional practice artifacts. No API key, external account or provider call is needed for the local checks.

- [Four flashcard notes](flashcards.txt): UTF-8 text with real tabs; source-check the cards, then use a fresh two-field practice deck and inspect the Anki import preview and finished notes. Local format validation does not establish a successful native import.
- [Printable calendar](calendar.html): February–April 2028, A4 landscape, 10 mm margins. No holiday claims. Check the PDF and print scale.
- [Local browser tool](local-tool.html): run from a local HTTP origin to test browser-specific persistence and export. Data is fictional and stays in that browser profile. It is not a hosted/shared account.
- [Reference checks](reference.py) and [tests](test_reference.py): identifier, exact boundary and flashcard validation.
- [Disposable Git rehearsal](git-rehearsal.py): creates its own temporary repository, saves two commits, checks a diff and restores an edit. It touches no existing repository and has no remote.
- [Current capability register](CAPABILITIES.md): official documentation and scoped recent research, reviewed November 1, 2026. Check actual account access before a live trial.

From this directory, run:

```sh
python3 reference.py
python3 -m unittest -v test_reference.py
python3 git-rehearsal.py
```

For the browser page, from this directory run `python3 -m http.server 8765 --bind 127.0.0.1` and open `http://127.0.0.1:8765/local-tool.html`. Stop the server with Ctrl-C after the exercise. This serves the current directory locally; do not start it from a directory containing private material. Use a different free port if needed.

The media directory contains original constructed reference material, with generation method and source scripts identified in its manifest. It is not evidence of a live generative-provider run, a listener test or rights clearance for another person's material. Preserve source and edited copies. Record actual listening, viewing and native-application trials separately.
