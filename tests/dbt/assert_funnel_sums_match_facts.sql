select m.emails_sent, f.sends, m.human_replies, r.replies
from (select sum(emails_sent) as emails_sent, sum(human_replies) as human_replies from {{ ref('mart_weekly_funnel') }}) m,
     (select count(*) as sends from {{ ref('fact_sends') }}) f,
     (select count(*) as replies from {{ ref('fact_replies') }} where is_human_reply) r
where m.emails_sent <> f.sends or m.human_replies <> r.replies
