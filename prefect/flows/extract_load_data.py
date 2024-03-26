"""
This module contains a Prefect flow for fetching news articles sentiment data and market data
from the APIs for a specified time range, pre-processing it and uploading it to GCS.
"""
import time
from datetime import timedelta, date, datetime, time as dt_time
import pandas as pd
import requests

from prefect_gcp.cloud_storage import GcsBucket
from prefect.artifacts import create_table_artifact
from prefect import flow, task


@task(name="Get Sentiment Data", retries=1, retry_delay_seconds=61, log_prints=True)
def get_news_sentiments(
    start_date: date,
    api_key: str,
) -> pd.DataFrame:
    """
    Fetches sentiment data for crypto news articles for a specified time range from the
    Alpha Vantage API.

    Args:
        start_date: The start date of the time range to retrieve.
        api_key: The API key required to access the data.

    Returns:
        pd.DataFrame: A Pandas dataframe containing the extracted data for each news article.
    """

    # Define the API endpoint URL with the necessary parameters
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "blockchain",
        "apikey": api_key,
        "time_from": start_date.strftime("%Y%m%d") + "T0000",
        "time_to": start_date.strftime("%Y%m%d") + "T2359",
        "sort": "RELEVANCE",
        "limit": "200",
    }

    # Send a GET request to the API endpoint and parse the JSON response
    print(
        f'Requesting news sentiments from Alpha Vantage for {start_date.strftime("%Y-%m-%d")}'
    )

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: Request failed with status code {response.status_code}")

    # Extract the relevant data for each article and store it in a list of dictionaries
    data = response.json()
    articles_data = [
        {
            "title": article["title"],
            "url": article["url"],
            "published_at": datetime.strptime(
                article["time_published"], "%Y%m%dT%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "source": article["source"],
            "source_domain": article["source_domain"],
            "relevance_score": next(
                (
                    t["relevance_score"]
                    for t in article["topics"]
                    if t["topic"] == "Blockchain"
                ),
                None,
            ),
            "overall_sentiment_score": article["overall_sentiment_score"],
            "overall_sentiment_label": article["overall_sentiment_label"],
            "ticker_sentiment": article["ticker_sentiment"],
        }
        for article in data["feed"]
    ]

    # Send the extracted data to Prefect Cloud as an artifact
    create_table_artifact(
        key="news-sentiments",
        table=articles_data,
        description="News Sentiments from Alpha Vantage",
    )

    # Convert the sentiment data to a Pandas dataframe
    sentiments_df = pd.DataFrame(articles_data).astype(
        {
            "published_at": "datetime64[ns]",
            "relevance_score": "float64",
            "overall_sentiment_score": "float64",
        }
    )

    # Return the Pandas dataframe from the extracted data
    return sentiments_df


@task(name="Get Token List", retries=3, retry_delay_seconds=61, log_prints=True)
def get_token_list() -> pd.DataFrame:
    """
    Fetches a list of cryptocurrency tokens from the CoinGecko API.
    Returns:
        List[str]: A list of cryptocurrency tokens.
    """

    # Send a GET request to the API endpoint and parse the JSON response
    print("Requesting list of supported tokens from CoinGecko")
    response = requests.get(
        url="https://api.coingecko.com/api/v3/coins/list",
        timeout=10,
    )

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: Request failed with status code {response.status_code}")

    data = response.json()

    # Tranform the CoinGecko data and clean it
    token_ids_df = pd.DataFrame(data)
    token_ids_df = token_ids_df.rename(columns={"id": "coingecko_id"})
    token_ids_df = token_ids_df.drop_duplicates(subset=["symbol"])
    token_ids_df["symbol"] = token_ids_df["symbol"].str.upper().dropna()
    token_ids_df = token_ids_df.reset_index(drop=True)

    # Get the list of supported tokens from Alpha Vantage and clean it
    print("Requesting list of supported tokens from Alpha Vantage")
    token_list_df = pd.read_csv(
        filepath_or_buffer="http://www.alphavantage.co/digital_currency_list/",
        storage_options={"User-Agent": "Mozilla/5.0"},
    )
    token_list_df = token_list_df.rename(columns={"currency code": "symbol"})
    token_list_df = token_list_df.drop_duplicates(subset=["symbol"])
    token_list_df = token_list_df.drop(columns=["currency name"])
    token_list_df["symbol"] = token_list_df["symbol"].str.upper().dropna()
    token_list_df = token_list_df.reset_index(drop=True)

    # Merge the two dataframes
    tokens_df = pd.merge(
        token_ids_df,
        token_list_df,
        how="inner",
        on="symbol",
    ).reset_index(drop=True)

    # Send the extracted data to Prefect Cloud as an artifact
    create_table_artifact(
        key="token-list",
        table=tokens_df.to_dict(orient="list"),
        description="List of tokens to get market performance for",
    )

    return tokens_df


@task(name="Get Market Data", retries=1, retry_delay_seconds=61, log_prints=True)
def get_market_data(
    start_date: float,
    end_date: float,
    coingecko_id: str,
    symbol: str,
) -> pd.DataFrame:
    """
    Fetches the price data from CoinGecko API for each token in the given list for
    a given time period.
    """

    # Send a GET request to the API endpoint and parse the JSON response
    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": datetime.combine(start_date, dt_time.min).timestamp(),
        "to": datetime.combine(end_date, dt_time.min).timestamp(),
    }

    print(f"Requesting {coingecko_id} market data for {start_date} to {end_date}")
    response = requests.get(
        url=url,
        params=params,
        timeout=10,
    )

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: Request failed with status code {response.status_code}")
        return None

    data = response.json()

    # Extract the relevant data for each metric and store it in a list of dictionaries
    prices_data = [
        {
            "date": datetime.utcfromtimestamp(int(price[0]) / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "price": price[1],
        }
        for price in data["prices"]
    ]

    market_caps_data = [
        {
            "date": datetime.utcfromtimestamp(int(market_cap[0]) / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "market_cap": market_cap[1],
        }
        for market_cap in data["market_caps"]
    ]

    volumes_data = [
        {
            "date": datetime.utcfromtimestamp(int(volume[0]) / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "volume": volume[1],
        }
        for volume in data["total_volumes"]
    ]

    # Merge the three lists of dictionaries into a single dataframe
    market_data_df = pd.merge(
        pd.DataFrame(prices_data),
        pd.DataFrame(market_caps_data),
        on="date",
        how="inner",
    ).merge(
        pd.DataFrame(volumes_data),
        on="date",
        how="inner",
    )

    market_data_df = market_data_df.astype(
        {
            "date": "datetime64[ns]",
            "price": "float64",
            "market_cap": "float64",
            "volume": "float64",
        }
    )

    market_data_df["symbol"] = symbol

    # Send the extracted data to Prefect Cloud as an artifact
    create_table_artifact(
        key="prices",
        table=market_data_df.to_dict(orient="list"),
        description="Market performance data",
    )

    return market_data_df


@flow(name="Process New Sentiments", log_prints=True)
def proces_news_sentiments(
    start_date: date,
    end_date: date,
    block_name: str,
    av_api_key: str,
) -> None:
    """
    Fetches the news sentiment data from Alpha Vantage API for each token in the given list for
    a given time period.
    """

    # Load the GCS bucket
    gcs_bucket = GcsBucket.load(block_name)

    # Iterate through each day in the time range, and extract, transform and upload the daily data
    while start_date < end_date:

        try:
            sentiments_df = get_news_sentiments(
                start_date,
                av_api_key,
            )
        except Exception:
            print(
                f"Error: Failed to get news sentiments for {start_date.strftime('%Y-%m-%d')}"
            )
            continue

        gcs_bucket.upload_from_dataframe(
            sentiments_df,
            f'sentiments/{start_date.strftime("%Y-%m-%d")}',
            "parquet_gzip",
        )

        print(
            f"Uploaded {start_date.strftime('%Y-%m-%d')} sentiments to GCS bucket {block_name}"
        )

        start_date += timedelta(days=1)

        time.sleep(12)

    return


@flow(name="Process Token Market Data", log_prints=True)
def process_market_data(
    start_date: date,
    end_date: date,
    block_name: str,
) -> None:
    """
    Fetches the price data from CoinGecko API for each token in the given list for
    a given time period.
    """

    # Load the GCS bucket
    gcs_bucket = GcsBucket.load(block_name)

    try:
        tokens_df = get_token_list()
    except Exception:
        print("Failed to get token list")
        return

    gcs_bucket.upload_from_dataframe(
        tokens_df,
        "tokens/names",
        "parquet_gzip",
    )

    print(f"Uploaded token list to GCS bucket {block_name}")

    tokens = tokens_df[["coingecko_id", "symbol"]].values.tolist()

    for coingecko_id, symbol in tokens:
        try:
            market_data_df = get_market_data(
                start_date,
                end_date,
                coingecko_id,
                symbol,
            )
        except Exception:
            print(f"Failed to get market data for {symbol}")
            continue

        gcs_bucket.upload_from_dataframe(
            market_data_df,
            f'prices/{symbol}/{start_date.strftime("%Y-%m-%d")}--{end_date.strftime("%Y-%m-%d")}',
            "parquet_gzip",
        )

        print(f"Uploaded {symbol} market data to GCS bucket {block_name}")

        time.sleep(7)

    return


@flow(name="EL Data", log_prints=True)
def extract_load_data(
    start_date: date,
    end_date: date,
    block_name: str,
    av_api_key: str,
) -> None:
    """
    Orchestrates the EL process for the given time period.
    """

    proces_news_sentiments(start_date, end_date, block_name, av_api_key)
    process_market_data(start_date, end_date, block_name)
    return
