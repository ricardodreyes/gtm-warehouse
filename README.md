# gtm-warehouse

A small dimensional warehouse on dbt-core and DuckDB over my own cold outreach data. It runs on a schedule, reruns to identical row counts, and every number in it can be checked against the campaign tracker it came from.

I built it because the data is mine and I know what every column means. Signet is a PII redaction proxy for Shopify AI apps that I sell by cold email to the developers who publish those apps. The warehouse is the send log, the lead list, and the inbox, modeled properly.

## What the data is

Four files, copied into `raw/<date>/` on every run:

| file | grain | rows |
|---|---|---|
| `merged.json` | one Shopify app listing, scraped and tiered | 487 |
| `verify-input.csv` | one contact address, with its outreach status | 167 |
| `sent.txt` | one email sent (date, message type, address, bounce or Message-ID) | 96 |
| `replies.txt` | one inbound message (date, kind, address) | 10 |

96 emails went to 79 addresses between 2026-08-13 and 2026-09-09 across three sequences. 7 bounced. 10 things came back, 9 of them helpdesk auto-acks, a canned redirect, and a ticket close. 1 was a person answering the question. That is the whole dataset.

The raw files are not in the repo. They are the campaign's working files and they name who I emailed. The aggregate marts are exported to `exports/` and those are committed.

## Schema

```
                      dim_date
                         |
 dim_campaign --- fact_sends --- dim_lead (SCD type 2)
                      |
                 fact_replies (incremental, 14-day lookback)
                      |
        mart_weekly_funnel   mart_reply_rate_by_message_type   mart_ml_training_set
```

`dim_lead` is a dbt snapshot. A lead gets a new version when its tier, contact address, address confidence, verification result, or outreach status changes. `fact_sends` carries the lead version in effect on the send date. `fact_replies` attributes each inbound message to the latest first-touch email to that address, which is the tracker's rule too.

`docs/model.md` has the grain of every table and why I picked it, including the candidate I rejected. `dbt docs generate` builds the lineage graph from the same descriptions.

## How to run it

```
uv sync
bin/run.sh                  # snapshot raw files, dbt build, log to logs/
uv run dbt build            # models, snapshot, seeds, tests: 90 checks
uv run python -m unittest tests/test_late_reply.py
```

`bin/run.sh` needs the source files at `~/signet/outreach/app-leads` or wherever `GTM_RAW_SRC` points. Without them, `uv run dbt build` still works against the last snapshot under `raw/`.

Every model has a description and at least one test. Two of the tests matter more than the rest: `assert_send_counts_match_log` fails if a send is dropped or duplicated between the raw log and the fact, and `assert_funnel_sums_match_facts` fails if the weekly mart drifts from the facts it rolls up.

## Rerun-safe

`bin/check-idempotent.sh` runs the pipeline twice and diffs row counts per relation. This is the output from 2026-09-13:

```
relation	run1	run2
main.campaigns	3	3
main.dim_campaign	3	3
main.dim_date	579	579
main.dim_lead	487	487
main.fact_replies	10	10
main.fact_sends	96	96
main.mart_ml_training_set	79	79
main.mart_reply_rate_by_message_type	4	4
main.mart_weekly_funnel	5	5
main.message_types	4	4
main_snapshots.snap_leads	487	487
main_staging.stg_lead_status	167	167
main_staging.stg_leads	487	487
main_staging.stg_replies	10	10
main_staging.stg_sends	96	96

identical row counts across two consecutive runs
```

The late-arriving fact is the reply. A person answers days after the send, sometimes after the next run has already happened. `fact_replies` is incremental with a 14-day lookback, so each run reprocesses the window and picks the reply up. `tests/test_late_reply.py` proves it: build with the one human reply removed from the raw file, put it back, run again, and the row count moves by exactly one. A third run leaves it there.

## Scheduled

`deploy/dev.ricardoreyes.gtm-warehouse.plist` runs `bin/run.sh` every morning at 07:15 through launchd on my Mac, logging to `logs/`. Install with:

```
cp deploy/dev.ricardoreyes.gtm-warehouse.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/dev.ricardoreyes.gtm-warehouse.plist
```

On Linux it is one cron line: `15 7 * * * /path/to/gtm-warehouse/bin/run.sh`.

## The ML mart

`mart_ml_training_set` is one row per lead that got a first-touch email, with what I knew about the lead before sending (tier, whether the listing declares protected customer data, address verification, rating, review count, launch year, category count, which sequence) and the label `replied`.

`ml/train.py` fits an XGBoost classifier on it and appends a run to `ml/runs.jsonl`. The honest number is 79 rows and 1 positive. No held-out fold can contain a positive, so there is no out-of-sample AUC to report, and the script logs `auc: null` with that reason. The wiring is there and waits on data. When the mart has 5 replies the same script switches to 5-fold stratified cross-validation on its own.

## Reply rate

| message type | sent | bounced | delivered | human replies |
|---|---|---|---|---|
| pitch (variant B) | 20 | 2 | 18 | 0 |
| research (discovery) | 40 | 5 | 35 | 0 |
| pitch-c (variant C) | 19 | 0 | 19 | 1 |
| pitch-c-t2 (touch 2) | 17 | 0 | 17 | 0 |

No type has passed 50 sends, so the rates are noise and the mart carries a description saying so. The rates need a volume the campaign hasn't reached, though. The dataset underneath is clean.

## Not in it, and why

- **No payments fact.** Signet has no paying customers, so there is no Stripe export to load. I'd rather the table not exist than fake one.
- **No opens or clicks.** The emails carry no tracking pixel on purpose (the product's pitch is that PII never leaves the customer's control). Send, bounce, and reply are the only observable events.
- **Replies are transcribed.** The sending mailbox is IMAP only, so `replies.txt` was written from the dated rows in the campaign tracker rather than pulled by a script. Every row traces to a tracker line. Rebuilding it from IMAP is the obvious next step.
- **S3 and a Tableau Public dashboard** are set up by `deploy/wizard.sh` and are not done yet. `marts/export.sql` writes the CSVs the dashboard reads; `docs/tableau.md` is the walkthrough. Until they exist, this README does not claim them.

## Layout

```
models/staging/     typed views over the raw files, sources declared
snapshots/          snap_leads, the SCD type 2 history behind dim_lead
models/dims/        dim_lead, dim_date, dim_campaign
models/facts/       fact_sends, fact_replies
models/marts/       weekly funnel, reply rate by message type, ML training set
seeds/              campaigns and the message type map
tests/dbt/          singular tests across tables
tests/              the late-reply unittest
bin/                run.sh, check-idempotent.sh, row-counts.sh
deploy/             launchd plist, the S3 and Tableau wizard
ml/                 train.py and runs.jsonl
marts/export.sql    CSV export for the dashboard
docs/               model.md, tableau.md
```

MIT.
