FROM prefecthq/prefect:2-python3.10

ENV PATH="/root/.local/bin:${PATH}"

ARG PREFECT_API_KEY
ENV PREFECT_API_KEY=$PREFECT_API_KEY

ARG PREFECT_API_URL
ENV PREFECT_API_URL=$PREFECT_API_URL

ENV PYTHONUNBUFFERED True

COPY prefect/flows /opt/prefect/flows/

COPY pyproject.toml poetry.lock /

RUN apt-get update -qq && \
    apt-get -qq install \
    curl

RUN curl -sSL https://install.python-poetry.org | python - \
    && poetry config virtualenvs.create false --local \
    && poetry install --without dev --no-root

ENTRYPOINT ["prefect", "agent", "start", "--pool", "default-agent-pool"]
