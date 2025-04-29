FROM python:3.13-alpine

WORKDIR /app

# Instalar dependências do sistema, incluindo tshark e libs necessárias
RUN apk add --no-cache \
    tshark \
    libpcap \
    libffi-dev \
    openssl-dev \
    gcc \
    musl-dev \
    linux-headers

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação
COPY . .
