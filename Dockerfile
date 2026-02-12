FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt update && apt install -y curl

RUN curl -sSf https://atlasgo.sh | sh
COPY atlas.hcl /root/atlas/atlas.hcl
COPY migrations /root/atlas/migrations

COPY ./src /app
COPY pyproject.toml /app

RUN uv pip compile pyproject.toml > requirements.txt
RUN uv pip install --system -r requirements.txt

CMD ["uv", "run", "uvicorn", "presentation.api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
