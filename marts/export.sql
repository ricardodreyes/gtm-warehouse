-- Export the marts to CSV for Tableau. Run from the repo root:
--   duckdb warehouse/gtm.duckdb -readonly < marts/export.sql
copy (select * from mart_weekly_funnel order by week_start) to 'exports/mart_weekly_funnel.csv' (header, delimiter ',');
copy (select * from mart_reply_rate_by_message_type order by first_sent_on) to 'exports/mart_reply_rate_by_message_type.csv' (header, delimiter ',');
copy (select * from mart_ml_training_set order by sent_on, slug) to 'exports/mart_ml_training_set.csv' (header, delimiter ',');
copy (select campaign_id, campaign_name, variant, call_to_action, touches, first_sent_on from dim_campaign order by first_sent_on) to 'exports/dim_campaign.csv' (header, delimiter ',');
