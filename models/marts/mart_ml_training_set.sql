with first_touch as (
    select slug, lead_key, campaign_id, address, sent_on, bounced
    from {{ ref('fact_sends') }}
    where touch_number = 1
    qualify row_number() over (partition by slug order by sent_on, campaign_id) = 1
),

replied as (
    select distinct slug
    from {{ ref('fact_replies') }}
    where is_human_reply
)

select
    f.slug,
    f.sent_on,
    f.campaign_id,
    l.tier,
    l.declares_protected_customer_data,
    l.has_ai_signal,
    l.email_confidence,
    l.verify_result,
    l.rating,
    l.review_count,
    year(l.launched_on) as launched_year,
    l.category_count,
    split_part(f.address, '@', 1) as mailbox_role,
    f.bounced,
    r.slug is not null as replied
from first_touch f
join {{ ref('dim_lead') }} l on l.lead_key = f.lead_key
left join replied r on r.slug = f.slug
