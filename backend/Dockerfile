FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000
