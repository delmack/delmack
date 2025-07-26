#!/bin/bash

# 1. Configurar o ambiente
export DEPLOYMENT_TARGET=/home/site/wwwroot
export VENV_PATH=$DEPLOYMENT_TARGET/antenv

# 2. Criar um ambiente virtual limpo
echo "A criar ambiente virtual em $VENV_PATH..."
python3.13 -m venv $VENV_PATH

# 3. Ativar o ambiente virtual
source $VENV_PATH/bin/activate

# 4. Instalar as dependências
echo "A instalar dependências do requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Desativar o ambiente virtual
deactivate

# 6. Copiar os ficheiros da aplicação
echo "A copiar ficheiros da aplicação..."
cp -r ./* $DEPLOYMENT_TARGET
