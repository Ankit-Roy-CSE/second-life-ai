FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared-py first (less frequently changed)
COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

# Install service dependencies
COPY services/grading/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy service code
COPY services/grading/app ./app

# Copy Alembic files
COPY services/grading/alembic ./alembic
COPY services/grading/alembic.ini ./alembic.ini

EXPOSE 8002

# Run migrations then start the service
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8002"]
