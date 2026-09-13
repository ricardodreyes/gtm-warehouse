select f.n as fact_rows, s.n as staging_rows
from (select count(*) as n from {{ ref('fact_sends') }}) f,
     (select count(*) as n from {{ ref('stg_sends') }}) s
where f.n <> s.n
