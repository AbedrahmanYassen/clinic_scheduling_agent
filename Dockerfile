FROM python:3.11-slim AS builder

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl-dev \
    openssl \        
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

RUN useradd -m -u 1000 appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Force TLS 1.2+ and update SSL certs
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY ./app /code/app

RUN chown -R appuser:appuser /code

USER appuser

EXPOSE 80

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]