{{
    config(
        materialized='incremental',
        unique_key='reply_id',
        incremental_strategy='delete+insert'
    )
}}

with replies as (
    select reply_id, received_on, kind, address
    from {{ ref('stg_replies') }}
    {% if is_incremental() %}
    where received_on >= (
        select coalesce(max(received_on), date '1970-01-01') from {{ this }}
    ) - interval {{ var('reply_lookback_days') }} day
    {% endif %}
),

attributed as (
    select
        r.reply_id,
        r.received_on,
        r.kind,
        r.address,
        s.send_id,
        s.lead_key,
        s.slug,
        s.campaign_id,
        s.message_type,
        s.sent_on
    from replies r
    left join {{ ref('fact_sends') }} s
        on s.address = r.address
        and s.touch_number = 1
        and s.sent_on <= r.received_on
    qualify row_number() over (partition by r.reply_id order by s.sent_on desc) = 1
)

select
    reply_id,
    send_id,
    lead_key,
    slug,
    campaign_id,
    received_on as date_day,
    received_on,
    kind,
    kind = 'reply' as is_human_reply,
    address,
    message_type,
    sent_on,
    received_on - sent_on as days_to_reply
from attributed
