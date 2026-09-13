with lines as (
    select string_split(trim(line), ' ') as t
    from {{ source('app_leads', 'replies') }}
    where line not like '#%' and trim(line) <> ''
)
select
    md5(t[1] || '|' || t[2] || '|' || lower(t[3])) as reply_id,
    t[1]::date as received_on,
    t[2] as kind,
    lower(t[3]) as address
from lines
