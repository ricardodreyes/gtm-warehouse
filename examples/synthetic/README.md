# Synthetic outreach data

These five fictional app listings use reserved example.com addresses. Every value is invented for a reproducible demo; none is a real prospect or campaign result.

There are six sends, one bounce, one automatic response, and one human reply. Delta replies after a follow-up; the model attributes it to the earlier first touch. The reply arrives seven days after that first touch.

From the repository root, run `uv sync` and `uv run python bin/demo.py`. The demo builds a temporary database, checks the expected results and repeat-run hashes, and removes the temporary database when finished. It does not read `raw/`, `.env`, a mailbox, or the production database. The fixed September 2026 dates match the model's date dimension.

`uv run python -m unittest discover -s tests -p 'test_*.py'` checks that a late reply is picked up once by the incremental model.
