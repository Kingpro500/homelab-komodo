FROM python:3.13-alpine

WORKDIR /app
COPY exporter.py /app/exporter.py

USER nobody
EXPOSE 9100
ENTRYPOINT ["python", "/app/exporter.py"]
