{% snapshot snap_leads %}
{{
    config(
        unique_key='slug',
        strategy='check',
        check_cols=['tier', 'contact_email', 'email_confidence', 'verify_result', 'status'],
        schema='snapshots'
    )
}}
select
    l.*,
    coalesce(s.status, 'none') as status
from {{ ref('stg_leads') }} l
left join {{ ref('stg_lead_status') }} s on s.contact_email = l.contact_email
{% endsnapshot %}
