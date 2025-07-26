#!/bin/bash

# Diretório de destino no App Service
DEPLOYMENT_TARGET=/home/site/wwwroot

# Caminho para o ambiente virtual
VENV_PATH=$DEPLOYMENT_TARGET/antenv

echo "A criar ambiente virtual em $VENV_PATH..."
python3.13 -m venv $VENV_PATH

echo "A ativar ambiente e a instalar dependências..."
# Ativar o ambiente virtual
source $VENV_PATH/bin/activate

# Atualizar o pip e instalar pacotes
pip install --upgrade pip
pip install -r requirements.txt

# Desativar para limpar o ambiente do script de deploy
deactivate

echo "A criar o script de arranque final (run.sh)..."
# Criar o script que o Azure irá realmente executar
cat <<EOF > $DEPLOYMENT_TARGET/run.sh
#!/bin/bash
echo "A ativar o ambiente virtual para o arranque..."
source $VENV_PATH/bin/activate
echo "A iniciar o Gunicorn..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
EOF

# Tornar o script de arranque executável
chmod +x $DEPLOYMENT_TARGET/run.sh

echo "Script de deploy concluído."
