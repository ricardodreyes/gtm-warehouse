select slug, count(*) as current_versions
from {{ ref('dim_lead') }}
where is_current
group by slug
having count(*) <> 1
