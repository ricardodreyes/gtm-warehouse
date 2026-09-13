select
    campaign_id,
    campaign_name,
    variant,
    call_to_action,
    touches,
    first_sent_on,
    description
from {{ ref('campaigns') }}
