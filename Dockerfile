# Estágio de build
FROM python:3.10-slim as builder

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Estágio de produção
FROM python:3.10-slim

WORKDIR /app

# Copiar dependências do estágio de build
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copiar a aplicação do estágio de build
COPY --from=builder /app .

# Expor a porta
EXPOSE 5002

# Comando para rodar a aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "src.main:create_app()"]