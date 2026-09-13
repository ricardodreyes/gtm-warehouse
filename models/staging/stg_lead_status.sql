select
    lower(trim(email)) as contact_email,
    priority::integer as priority,
    status,
    slug,
    app as app_name,
    source as email_source
from {{ source('app_leads', 'verify_input') }}
