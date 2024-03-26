# Crypto Market Sentiment Data Pipeline & Analysis

This project attempts to engineer a comprehensive Extract, Load, Transform (ELT) data pipeline on the cryptocurrency market & sentiment data within the Google Cloud Platform (GCP).

The pipeline is configured to process sentiment and market data daily for more than 500 of the largest cryptocurrencies and make it available for fear-and-greed analysis. It is also capable of collecting historical data for any time range.

To achieve this, various tools such as Prefect, Cloud Storage, BigQuery, dbt, Superset, and others are utilized.

## Purpose of this Project

Obtaining comprehensive historical data and news articles for cryptocurrency market is a challenging and often costly task. While various API providers offer similar services, they either lack free plans or impose significant restrictions on the available information and request limits.

This fully automated data pipeline addresses this issue by fetching daily and historical data from multiple providers, including Alpha Vantage and CoinGecko. By default, the pipeline retrieves daily current data and enables users to retrieve historical records for any desired time period.

This pipeline is developed to be fully hosted on GCP and is orchestrated with Prefect, so it doesn't require any manual involvolvement. The section below describes its inner workings in greater detail.

## Tech Stack

- **Python**: Manages the data extraction, pre-processing, loading, and transformation routines.
- **Pandas**: Cleans, manipulates, and pre-processes data retrieved from third-party APIs to prepare it for ingestion into the data lake.
- **Alpha Vantage API**: Provides daily sentiment data from news related to the blockchain topic.
- **CoinGecko API**: Offers market data for all cryptocurrencies mentioned in the news within a specified time range.
- **Prefect Cloud**: Orchestrates all code flows and facilitates real-time monitoring of their performance.
- **Terraform**: Sets up the GCP infrastructure and provisions the essential services listed below.
- **Docker**: Containerizes the code to build the Prefect agent VM and Cloud Run jobs.
- **Compute Engine**: Executes the Prefect agent VM responsible for fetching daily jobs and sending them to Cloud Run.
- **Artifact Registry**: Stores the Docker images required for building the Prefect agent VM and Cloud Run jobs.
- **Cloud Run**: Receives and executes daily jobs in a serverless environment.
- **Cloud Storage**: Functions as a staging area for raw market and token data.
- **BigQuery**: Serves as the primary data warehouse, storing external tables from the GCS bucket and partitioned tables from dbt models.
- **dbt Core**: Transforms and partitions data in BigQuery, enabling query capabilities for Superset.
- **GitHub**: Hosts the source code and enables continuous integration and deployment using GitHub Actions.
- **Apache Superset**: Constructs analytics dashboards and visualizations for comprehensive analysis.

## Data Pipeline Architecture

![Data Architecture Diagram](https://github.com/kkuznets/crypto-fear-and-greed-analysis/assets/60260298/6713164e-ca23-4206-9a41-961a4fa8dd7f)

## Dashboard Example

<img width="1438" alt="SH 2023-05-05 at 1 16 16 am" src="https://user-images.githubusercontent.com/60260298/236252056-0af255b0-18c6-475d-8a13-b6cddf7b0607.png">

## Example Findings

1. After conducting an investigation into the correlation between public sentiment and specific tokens (primarily BTC, ETH, and MATIC), it was observed that positive news articles have a limited immediate impact on public opinion. Conversely, negative press leads to a significant and rapid decline in the public's perception of a cryptocurrency.
2. There appears to be an approximate one-month delay between the overall sentiment of a token becoming positive and the public's subsequent change in opinion. It is possible that a critical mass of positive news articles is required before people begin to take notice of a particular token again.
3. Stablecoins, due to their inherent nature, remain unaffected by negative press. However, instances where stablecoins have failed to maintain their intended price have resulted in extremely negative news sentiment in the past.

## Reproduction Steps

This project aims to make it as easy as possible to copy the pipeline over and start it up.

- Fork this repository.
- Ensure you already have a Google Cloud project that you can use. If you don't you can create it using [this guide](https://cloud.google.com/resource-manager/docs/creating-managing-projects) from Google.
- Create a new service account with the required permissions.
  - In the Google Cloud Console, click to `Activate Cloud Shell`.
  - In the Cloud Shell, click to `Open Editor`.
  - Save the following code as a file **setup.sh**. Don't forget to edit the name of your project. Run this file with commans `sh setup.sh` from the Cloud Shell terminal it will generate a new service account key file **sa_key.json** for you.

```bash
# Create GCP account + project
export CLOUDSDK_CORE_PROJECT="YOUR-PROJECT-NAME"
export CLOUDSDK_COMPUTE_REGION=us-central1
export GCP_SA_NAME=binance-transactions
export GCP_AR_REPO=binance-transactions

# enable required GCP services:
gcloud services enable iamcredentials.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable compute.googleapis.com

# create service account named after GCP_SA_NAME variable:
gcloud iam service-accounts create $GCP_SA_NAME
export MEMBER=serviceAccount:"$GCP_SA_NAME"@"$CLOUDSDK_CORE_PROJECT".iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/run.admin"
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/compute.instanceAdmin.v1"
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/bigquery.admin"
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/artifactregistry.admin"
gcloud projects add-iam-policy-binding $CLOUDSDK_CORE_PROJECT --member=$MEMBER --role="roles/iam.serviceAccountUser"

# create JSON credentials file as follows, then copy-paste its content into your GitHub Secret:
gcloud iam service-accounts keys create sa_key.json --iam-account="$GCP_SA_NAME"@"$CLOUDSDK_CORE_PROJECT".iam.gserviceaccount.com
```

- Copy the contents of the file **sa_key.json** that was generated in the previous step. Navigate to the Secrets & Actions section in yout GiHub repository settings and save the contents of this file as a secret **GCP_CREDENTIALS**.
- Navigate to Alpha Vantage [website](https://www.alphavantage.co/support/#api-key) and generate a free API key. Save this key as a secret **AV_API_KEY**.
- Create an Account in [Prefect Cloud 2.0](https://www.prefect.io/cloud/) if you haven't already. Create a new workspace, view your account's settings and create and copy the API url and API key for your new workspace. Save them as secrets **PREFECT_API_URL** and **PREFECT_API_KEY** respectively.
- Navigate to the GitHub Actions tab in your repository and click on action `Init Setup`. Start it with the variables that you prefer (or leave them default).
  - This step will prepare the GCP infrastructure for you, deploy the Python code to Prefect Cloud, and build and start the Prefect agent VM in order to run the Prefect flows.
  - If you edit the default variables, you might need to edit the dbt Core project settings and schema file in the folder to make sure they match all of the variables you edited.
- Once the previous step is finished, you can navigate back to your Prefect Cloud and view the flow deployments. Click on the deployment for the flow `Main Flow` and when its page opens, click to add a schedule that you prefer so that the data gets fetched regularly automatically.
- You can also click to `Custom Run` this deployment and specify the **start_date** and **end_date** parameters in order to fetch historical data for a time period of your choice. Make sure you enter them in the format **%Y%m%d**, i.e **20221127**.
- That's it! The transformed data will be available in BigQuery after the first deployment run. News sentiments data will be located in the table **sentiments_t** and token price information will be located in the table **prices_t**.
- If you make any changes to the Prefect flows, dbt Core models or GitHub Actions workflows, you should run the GitHub action `Reset Setup` that will re-build the Cloud Run jobs image and re-deploy Prefect flows.
- If you want to remove the whol setup for this project, you can run the GitHub action `Delete Setup` which will delete all GCP services that were created in the steps above.
