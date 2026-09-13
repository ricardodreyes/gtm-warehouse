with sends as (
    select
        s.send_id,
        s.sent_on,
        s.message_type,
        s.address,
        s.bounced,
        s.message_id,
        m.campaign_id,
        m.touch_number,
        coalesce(st.slug, first_lead.slug) as slug
    from {{ ref('stg_sends') }} s
    join {{ ref('message_types') }} m on m.message_type = s.message_type
    left join {{ ref('stg_lead_status') }} st on st.contact_email = s.address
    left join (
        select contact_email, min(slug) as slug
        from {{ ref('stg_leads') }}
        where contact_email is not null
        group by contact_email
    ) first_lead on first_lead.contact_email = s.address
),

versioned as (
    select
        sends.*,
        d.lead_key
    from sends
    join {{ ref('dim_lead') }} d on d.slug = sends.slug
    qualify row_number() over (
        partition by sends.send_id
        order by
            case when d.valid_from <= sends.sent_on::timestamp then 0 else 1 end,
            case when d.valid_from <= sends.sent_on::timestamp then d.valid_from end desc,
            d.valid_from asc
    ) = 1
)

select
    send_id,
    lead_key,
    slug,
    campaign_id,
    sent_on as date_day,
    sent_on,
    message_type,
    touch_number,
    address,
    bounced,
    not bounced as delivered,
    message_id
from versioned
