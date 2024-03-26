{{ config (
    materialized = "incremental"
    )
}} 

SELECT  
    CAST(date AS DATE) AS collected_at,
    * EXCEPT(date)
FROM
    {{ source (
            'crypto_data',
            'prices'
            )
    }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, TIMESTAMP_TRUNC(date, DAY) ORDER BY date DESC) = 1
    

{% if is_incremental() %}

  -- this filter will only be applied on an incremental run
  where date > (select max(date) from {{ this }})

{% endif %}