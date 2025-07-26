# 1. Usar a imagem base oficial do Python
FROM python:3.13-slim

# 2. Definir o diretório de trabalho dentro do contentor
WORKDIR /app

# 3. Copiar o ficheiro de dependências
COPY requirements.txt .

# 4. Instalar as dependências
# O --no-cache-dir é uma boa prática para manter a imagem pequena
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo o código da aplicação para o contentor
COPY . .

# 6. Expor a porta que a aplicação irá usar
EXPOSE 8000

# 7. O comando para executar a aplicação quando o contentor arrancar
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
