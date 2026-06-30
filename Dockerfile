# Etapa 1: compilación de dependencias
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Etapa 2: imagen de producción (sin herramientas de compilación)
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
