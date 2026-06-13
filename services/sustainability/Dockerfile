FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

COPY services/sustainability/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

COPY services/sustainability/app ./app

# COPY services/sustainability/alembic ./alembic
# COPY services/sustainability/alembic.ini ./alembic.ini

EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
