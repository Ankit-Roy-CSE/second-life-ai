FROM python:3.12-slim

WORKDIR /app

# Install shared-py first (editable install from monorepo mount)
COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

# Install service dependencies
COPY services/gateway/pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy service source
COPY services/gateway/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
