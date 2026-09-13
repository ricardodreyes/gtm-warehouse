select reply_id, days_to_reply
from {{ ref('fact_replies') }}
where days_to_reply < 0
