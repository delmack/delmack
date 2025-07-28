# Usar a imagem base oficial do Python (versão estável)
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do contentor
WORKDIR /app

# Copiar o ficheiro de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os outros ficheiros do projeto
COPY . .

# Expor a porta que a aplicação irá usar
EXPOSE 8000

# O comando para executar a aplicação quando o contentor arrancar
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:app"]