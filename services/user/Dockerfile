FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

COPY services/user/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

COPY services/user/app ./app

# Copy alembic config when migrations exist (added in P1-A1)
# COPY services/user/alembic ./alembic
# COPY services/user/alembic.ini ./alembic.ini

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
