# Data model

Why each table has the grain it has. Read this before adding a model.

## Sources and their grain

| Source | Grain | Key | Rows |
|---|---|---|---|
| `merged.json` | one Shopify app listing | `slug` | 487 |
| `verify-input.csv` | one contact address among tier A leads with a HIGH-confidence email | `email` | 167 |
| `sent.txt` | one email sent | `(sent_on, message_type, address)` | 96 |
| `replies.txt` | one inbound message | `(received_on, kind, address)` | 10 |

The send and reply logs have no time of day and no sequence number, so two emails of the same type to the same address on the same day would collide. A `unique` test on the hashed key fails the build the day that happens, which beats silently merging them.

`merged.json` is the end of a scrape and enrichment chain (`candidates.json`, 1,642 rows, then `listings.json` and `final.json`, 487) and carries every field the earlier files have, so it is the only lead source loaded. `sent.txt` is a cache of the sender's Gmail Sent folder; `replies.txt` is the same shape for the inbox, transcribed from the dated rows in the campaign tracker and rebuilt from IMAP when in doubt.

## The two candidates, and which one won

**Candidate 1, batch as the dimension.** `dim_campaign` at the grain of a send batch: one row per `(sent_on, message_type)`, ten rows. Every send joins to its batch. Rejected because a batch has no attributes beyond its date and type. That is a degenerate dimension in Kimball's sense, so it lives on the fact as `batch_date`.

**Candidate 2, the sequence as the dimension.** `dim_campaign` at the grain of an outreach sequence: `pitch-b`, `research`, `pitch-c`. Three rows with real attributes: the variant name, what the call to action was, how many touches the sequence has, the first send date. A touch-2 email (`pitch-c-t2` in the raw log) is the same campaign at `touch_number = 2`. Chosen. The reply-rate mart still groups by the raw message type, because that is the table the campaign tracker keeps and the number a reader wants to check against it.

A third shape, folding replies onto `fact_sends` as an accumulating snapshot, was dropped before sketching. Replies arrive days after sends, and keeping them as their own fact is what makes the late-arriving handling visible and testable.

## Dimensions

**`dim_lead`**, one row per lead per version. Source grain is one app listing, so the natural key is `slug`. Two apps can share one contact mailbox (three addresses do), so the address is not the key. A dbt snapshot with the `check` strategy versions the row whenever one of `tier`, `contact_email`, `email_confidence`, `verify_result`, or `status` changes. Those are the columns the outreach process rewrites: the tiering script recomputes `tier`, the verifier adds `verify_result`, and `status` moves from unsent to queued to sent to bounced. Descriptive columns (name, developer, rating, categories) are carried on the row but do not open a new version.

**`dim_date`**, one row per calendar day from 2026-06-01 through 2027-12-31, generated in SQL. Exists so weekly rollups agree on what a week is (ISO, Monday start) and so the funnel can show weeks with zero sends.

**`dim_campaign`**, one row per sequence, keyed by `campaign_id`. Defined in a seed because the attributes are editorial (what variant B was, that pitch C is a forward-ask) and the raw log only has the type token.

## Facts

**`fact_sends`**, one row per email sent. Keys: `lead_key` (the `dim_lead` version whose `valid_from` most recently precedes the send date, or the earliest version when the send predates the snapshot history; the address resolves to a slug through `verify-input.csv`, then by first slug), `campaign_id`, `date_day`. The snapshot history starts 2026-09-13, so every send loaded so far resolves to the first recorded version. That fallback records what was known after the send, and the training mart inherits the same limit. Measures and flags: `bounced`, `touch_number`, `message_id`. `message_type` and `batch_date` are degenerate dimensions.

**`fact_replies`**, one row per inbound message. `kind` separates a human reply from a helpdesk auto-ack, a canned redirect, and a ticket close; only `reply` counts in any rate. Each row attributes to the touch-1 send of the same address that most recently precedes it (ties broken by `send_id`), matching the tracker's rule that a reply to a follow-up logs against the original send. `days_to_reply` is measured from that send.

This is the late-arriving fact. The model is incremental with a 14-day lookback: every run reprocesses inbound rows dated within 14 days of the newest row already loaded, so a reply that lands three days after its send is picked up by the next scheduled run without a full rebuild. The window is anchored on the newest loaded reply, not on today. A row dated earlier than that window (a late transcription, a corrected date) needs `dbt build --full-refresh`. A mistyped future date would push the window forward and hide later rows. `tests/test_late_reply.py` proves it by loading the raw files with one reply removed, running, restoring the row, running again, and asserting the row count moved by one.

## Marts

**`mart_weekly_funnel`**, one row per ISO week. Leads first contacted, emails sent, bounces, delivered, human replies. Built on `dim_date` so silent weeks appear as zeros.

**`mart_reply_rate_by_message_type`**, one row per raw message type. Sends, bounced, delivered, replies, reply rate. Mirrors the tracker's "Sends by message type" table so the two can be diffed.

**`mart_ml_training_set`**, one row per lead that received a touch-1 send, with lead attributes from the dimension version the send resolved to (tier, PCD declaration, verification result, email confidence, rating, review count, launch year, category count, campaign) and the label `replied`. Bounces and replies are outcomes and stay out of the features. The set is small; see the README for what that means for the model.

## What is not modeled and why

No `fact_payments`: Signet has no paying customers and there is no payment export. No `dim_sender`: the raw log does not record which mailbox sent each email before 2026-09-01. No opens or clicks: cold emails carry no tracking pixel by decision (DECISIONS.md D-S06), so send, bounce, and reply are the only observable events.
