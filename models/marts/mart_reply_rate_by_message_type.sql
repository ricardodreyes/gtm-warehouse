with sends as (
    select
        message_type,
        campaign_id,
        touch_number,
        count(*) as sends,
        count(*) filter (where bounced) as bounced,
        count(*) filter (where delivered) as delivered,
        min(sent_on) as first_sent_on,
        max(sent_on) as last_sent_on
    from {{ ref('fact_sends') }}
    group by message_type, campaign_id, touch_number
),

replies as (
    select message_type, count(*) as human_replies
    from {{ ref('fact_replies') }}
    where is_human_reply
    group by message_type
)

select
    s.message_type,
    s.campaign_id,
    s.touch_number,
    s.sends,
    s.bounced,
    s.delivered,
    coalesce(r.human_replies, 0) as human_replies,
    round(coalesce(r.human_replies, 0) / nullif(s.delivered, 0), 4) as reply_rate,
    s.first_sent_on,
    s.last_sent_on
from sends s
left join replies r on r.message_type = s.message_type
order by s.first_sent_on
