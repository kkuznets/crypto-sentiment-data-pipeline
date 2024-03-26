{{ config (
    materialized = "incremental",
    partition_by = {
        "field": "published_at",
        "data_type": "timestamp",
        "granularity": "month"
        }
    )
}} 

WITH
sentiments_unnested AS (
    SELECT
        * EXCEPT(ticker_sentiment)
    FROM
        {{ source (
            'crypto_data',
            'sentiments'
            )
        }},
    UNNEST(ticker_sentiment[0])
),
tokens AS (
    SELECT
        symbol,
        name
    FROM
        {{ source (
            'crypto_data',
            'tokens'
            )
        }}
)

SELECT  
    su.published_at,
    su.title,
    su.url,
    su.source,
    su.source_domain,
    su.relevance_score AS overall_relevance_score,
    su.overall_sentiment_score,
    su.overall_sentiment_label,
    REPLACE(su.item.ticker, 'CRYPTO:', '') AS token,
    t.name AS token_name,
    CAST(su.item.relevance_score AS FLOAT64) AS token_relevance_score,
    su.item.ticker_sentiment_label AS token_sentiment_label,
    CAST(su.item.ticker_sentiment_score AS FLOAT64) AS token_sentiment_score,
FROM
    sentiments_unnested AS su
    INNER JOIN tokens AS t
        ON REPLACE(su.item.ticker, 'CRYPTO:', '') = t.symbol
WHERE
    STARTS_WITH(su.item.ticker, 'CRYPTO:')

{% if is_incremental() %}

  -- this filter will only be applied on an incremental run
  where published_at > (select max(published_at) from {{ this }})

{% endif %}