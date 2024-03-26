FROM python:3.10

ENV PATH="/root/.local/bin:${PATH}"

ARG PREFECT_API_KEY
ENV PREFECT_API_KEY=$PREFECT_API_KEY

ARG PREFECT_API_URL
ENV PREFECT_API_URL=$PREFECT_API_URL

ARG PREFECT_BLOCK
ENV PREFECT_BLOCK=$PREFECT_BLOCK

ARG GCP_CREDENTIALS
ENV GCP_CREDENTIALS=$GCP_CREDENTIALS

ARG GCP_PROJECT
ENV GCP_PROJECT=$GCP_PROJECT

ARG GCP_REGION
ENV GCP_REGION=$GCP_REGION

ARG DATASET_NAME
ENV DATASET_NAME=$DATASET_NAME

ARG BUCKET_NAME
ENV BUCKET_NAME=$BUCKET_NAME

ARG AV_API_KEY
ENV AV_API_KEY=$AV_API_KEY

ENV PYTHONUNBUFFERED True

WORKDIR /pipeline

COPY pyproject.toml poetry.lock /

RUN apt-get update -qq && \
    apt-get -qq install \
    curl \
    jq

RUN echo "$GCP_CREDENTIALS" | base64 --decode | jq > gcp_credentials.json

RUN curl -sSL https://install.python-poetry.org | python - \
    && poetry config virtualenvs.create false --local \
    && poetry install --without dev --no-root

RUN touch profiles.yaml && \
    echo "fear_and_greed:" >> profiles.yml && \
    echo "  outputs:" >> profiles.yml && \
    echo "    dev:" >> profiles.yml && \
    echo "      dataset: ${DATASET_NAME}" >> profiles.yml && \
    echo "      job_execution_timeout_seconds: 300" >> profiles.yml && \
    echo "      job_retries: 1" >> profiles.yml && \
    echo "      keyfile: ${PWD}/gcp_credentials.json" >> profiles.yml && \
    echo "      location: ${GCP_REGION}" >> profiles.yml && \
    echo "      method: service-account" >> profiles.yml && \
    echo "      priority: interactive" >> profiles.yml && \
    echo "      project: ${GCP_PROJECT}" >> profiles.yml && \
    echo "      threads: 4" >> profiles.yml && \
    echo "      type: bigquery" >> profiles.yml && \
    echo "  target: dev" >> profiles.yml
