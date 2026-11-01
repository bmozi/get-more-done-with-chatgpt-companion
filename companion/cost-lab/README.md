# A small fictional cost tool

Run `python3 companion/cost-lab/costs.py --visits 5` from the repository root. It compares complete exercise terms: A costs $20 per month plus $4 per visit; B costs $8 per visit. It prints JSON and returns no winner on a tie. There is no deposit, tax addition or other fee in this exercise.

Run `python3 -m unittest discover -s companion/cost-lab -p 'test_costs.py' -v` to check the known examples, a changed pair of plans and invalid inputs. These are local reference-program checks, not a captured Codex implementation session.

Chapter 30's optional exercise is to add a human-readable explanation without changing the existing calculation or JSON route. Work on a copy or separate branch, write a new acceptance example, inspect the diff and run both existing and new checks. No provider account is required to run the baseline.
