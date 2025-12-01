FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ./src /app
COPY pyproject.toml /app

RUN uv pip compile pyproject.toml > requirements.txt
RUN uv pip install --system -r requirements.txt

CMD uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload
