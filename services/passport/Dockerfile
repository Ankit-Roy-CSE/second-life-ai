FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

COPY services/passport/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

COPY services/passport/app ./app

# COPY services/passport/alembic ./alembic
# COPY services/passport/alembic.ini ./alembic.ini

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
