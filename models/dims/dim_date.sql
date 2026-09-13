with days as (
    select unnest(generate_series(date '2026-06-01', date '2027-12-31', interval 1 day))::date as date_day
)
select
    date_day,
    date_trunc('week', date_day)::date as week_start,
    isoyear(date_day) as iso_year,
    week(date_day) as iso_week,
    isoyear(date_day)::varchar || '-W' || lpad(week(date_day)::varchar, 2, '0') as iso_week_label,
    date_trunc('month', date_day)::date as month_start,
    year(date_day) as year,
    dayname(date_day) as day_name,
    isodow(date_day) in (6, 7) as is_weekend
from days
