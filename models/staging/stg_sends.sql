with lines as (
    select string_split(trim(line), ' ') as t
    from {{ source('app_leads', 'sent') }}
    where line not like '#%' and trim(line) <> ''
)
select
    md5(t[1] || '|' || t[2] || '|' || lower(t[3])) as send_id,
    t[1]::date as sent_on,
    t[2] as message_type,
    lower(t[3]) as address,
    coalesce(t[4] = 'bounced', false) as bounced,
    case when t[4] like '<%' then t[4] end as message_id
from lines
