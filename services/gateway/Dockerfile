FROM python:3.12-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared-py (copied from repo root context)
COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

# Install service-level pyproject
COPY services/gateway/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy service source
COPY services/gateway/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
