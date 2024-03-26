"""
This file contains the Prefect flow for transforming the data in BigGquery with DBT.
"""
import os
from prefect_gcp.bigquery import BigQueryWarehouse
from prefect_dbt import DbtCoreOperation
from prefect import flow, task


@task(name="Run dbt models", log_prints=True)
def run_dbt() -> None:
    """
    Runs the dbt models.
    """

    dbt_path = f"{os.getcwd()}/dbt/fear_and_greed"

    dbt_op = DbtCoreOperation(
        commands=["dbt build"],
        working_dir=dbt_path,
        project_dir=dbt_path,
        profiles_dir=os.getcwd(),
    )

    dbt_op.run()


@task(name="Create External Table", retries=3, log_prints=True)
def create_table(
    block_name: str,
    dataset_name: str,
    table_name: str,
    schema: str,
    bucket_name: str,
    folder_name: str,
) -> None:
    """
    Creates an external table in BigQuery.
    """
    print(f"Creating table {table_name} in dataset {dataset_name}")
    with BigQueryWarehouse.load(block_name) as warehouse:
        operation = f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {dataset_name}.{table_name} ({schema})
                OPTIONS (
                format = "PARQUET",
                uris = ['gs://{bucket_name}/{folder_name}/*']
                );
        """
        warehouse.execute(operation)
    print(f"Table {table_name} created in dataset {dataset_name}")

    return


@flow(name="Create Tables", log_prints=True)
def create_tables(
    block_name: str,
    dataset_name: str,
    bucket_name: str,
) -> None:
    """
    Creates the required tables in the BigQuery dataset.
    """

    schema = """
        date TIMESTAMP,
        symbol STRING,
        price FLOAT64,
        volume FLOAT64,
        market_cap FLOAT64
        """
    create_table(
        block_name=block_name,
        dataset_name=dataset_name,
        bucket_name=bucket_name,
        table_name="prices",
        folder_name="prices",
        schema=schema,
    )

    schema = """
        coingecko_id STRING,
        symbol STRING,
        name STRING
        """
    create_table(
        block_name=block_name,
        dataset_name=dataset_name,
        bucket_name=bucket_name,
        table_name="tokens",
        folder_name="tokens",
        schema=schema,
    )

    schema = """
        published_at TIMESTAMP,
        title STRING,
        url STRING,
        source STRING,
        source_domain STRING,
        relevance_score FLOAT64,
        overall_sentiment_score FLOAT64,
        overall_sentiment_label STRING,
        ticker_sentiment STRUCT<list ARRAY<STRUCT<item STRUCT<relevance_score STRING, ticker STRING, ticker_sentiment_label STRING, ticker_sentiment_score STRING>>>>
        """
    create_table(
        block_name=block_name,
        dataset_name=dataset_name,
        bucket_name=bucket_name,
        table_name="sentiments",
        folder_name="sentiments",
        schema=schema,
    )

    return


@flow(name="Transform Data", log_prints=True)
def transform_data(
    block_name: str,
    dataset_name: str,
    bucket_name: str,
) -> None:
    """
    Transforms the data in the BigQuery dataset.
    """

    create_tables(
        block_name=block_name,
        dataset_name=dataset_name,
        bucket_name=bucket_name,
    )

    run_dbt()

    return
