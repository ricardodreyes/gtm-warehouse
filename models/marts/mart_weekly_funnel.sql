with weeks as (
    select distinct week_start
    from {{ ref('dim_date') }}
    where date_day between (select min(sent_on) from {{ ref('fact_sends') }})
        and greatest(
            (select max(sent_on) from {{ ref('fact_sends') }}),
            coalesce((select max(received_on) from {{ ref('fact_replies') }}), date '1970-01-01')
        )
),

first_contact as (
    select slug, min(sent_on) as first_sent_on
    from {{ ref('fact_sends') }}
    group by slug
),

sends as (
    select
        d.week_start,
        count(*) as emails_sent,
        count(*) filter (where f.touch_number = 1) as first_touches,
        count(*) filter (where f.bounced) as bounced,
        count(*) filter (where f.delivered) as delivered
    from {{ ref('fact_sends') }} f
    join {{ ref('dim_date') }} d on d.date_day = f.date_day
    group by d.week_start
),

contacts as (
    select d.week_start, count(*) as leads_first_contacted
    from first_contact fc
    join {{ ref('dim_date') }} d on d.date_day = fc.first_sent_on
    group by d.week_start
),

replies as (
    select
        d.week_start,
        count(*) filter (where r.is_human_reply) as human_replies,
        count(*) filter (where not r.is_human_reply) as machine_responses
    from {{ ref('fact_replies') }} r
    join {{ ref('dim_date') }} d on d.date_day = r.date_day
    group by d.week_start
)

select
    w.week_start,
    isoyear(w.week_start)::varchar || '-W' || lpad(week(w.week_start)::varchar, 2, '0') as iso_week_label,
    coalesce(c.leads_first_contacted, 0) as leads_first_contacted,
    coalesce(s.emails_sent, 0) as emails_sent,
    coalesce(s.first_touches, 0) as first_touches,
    coalesce(s.bounced, 0) as bounced,
    coalesce(s.delivered, 0) as delivered,
    coalesce(r.human_replies, 0) as human_replies,
    coalesce(r.machine_responses, 0) as machine_responses
from weeks w
left join sends s on s.week_start = w.week_start
left join contacts c on c.week_start = w.week_start
left join replies r on r.week_start = w.week_start
order by w.week_start
