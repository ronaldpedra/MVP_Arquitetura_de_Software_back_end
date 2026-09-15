# Use uma imagem oficial do Python como imagem pai
FROM python:3.9-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de dependências para o diretório atual
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que o Flask vai rodar
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]
