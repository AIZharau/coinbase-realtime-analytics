FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY docker/consumer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary source files
COPY src/main/clickhouse_consumer.py /app/src/main/
COPY src/main/utils/ /app/src/main/utils/

CMD ["python", "src/main/clickhouse_consumer.py"]