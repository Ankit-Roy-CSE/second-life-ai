FROM python:3.12-slim

WORKDIR /app

COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

COPY services/lifecycle/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY services/lifecycle/app ./app

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
