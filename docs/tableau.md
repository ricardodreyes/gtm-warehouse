# Tableau Public walkthrough

The dashboard reads the CSVs that `marts/export.sql` writes to `exports/`. Refresh them after any run:

```
duckdb warehouse/gtm.duckdb -readonly < marts/export.sql
```

1. Open Tableau Public. Connect, Text file, `exports/mart_weekly_funnel.csv`.
2. Sheet "Weekly funnel": `week_start` on Columns (discrete), `emails_sent` and `delivered` on Rows as side-by-side bars, `human_replies` on a dual axis as a line.
3. Add `exports/mart_reply_rate_by_message_type.csv` as a second data source.
4. Sheet "Reply rate by message type": `message_type` on Rows, `sends`, `delivered`, `human_replies` as bars, `reply_rate` as a mark label.
5. Dashboard: both sheets, one text box with the caveat that no message type has passed 50 sends, so the rates are noise.
6. File, Save to Tableau Public. Copy the URL from the browser and paste it into the README under "Dashboard".

`bash deploy/wizard.sh` walks through this and the S3 bucket step by step.
