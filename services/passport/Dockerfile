FROM python:3.12-slim

WORKDIR /app

COPY packages/shared-py /packages/shared-py
RUN pip install --no-cache-dir /packages/shared-py

COPY services/passport/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY services/passport/app ./app

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
