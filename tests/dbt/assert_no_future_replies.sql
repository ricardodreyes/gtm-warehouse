select reply_id, received_on
from {{ ref('stg_replies') }}
where received_on > current_date
