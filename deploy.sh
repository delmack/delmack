#!/bin/sh

# Este script é executado a partir da raiz do código fonte no Kudu.
# O Oryx executa o build num diretório de origem e move para um de destino.

# Variáveis de ambiente fornecidas pelo Kudu/Oryx
# DEPLOYMENT_SOURCE é onde o nosso código está (ex: /tmp/8ddcc5...)
# DEPLOYMENT_TARGET é para onde o resultado final deve ir (ex: /home/site/wwwroot)

echo "--- Início do Script de Deploy Personalizado ---"

# 1. Executar o build do Oryx para criar o ambiente virtual e instalar as dependências
# Isto irá criar o ambiente 'antenv' dentro de $DEPLOYMENT_TARGET
echo "A executar o build do Oryx..."
oryx build $DEPLOYMENT_SOURCE -o $DEPLOYMENT_TARGET --platform python --platform-version 3.13

# Verificar se o build do Oryx foi bem sucedido
if [ $? -ne 0 ]; then
  echo "O build do Oryx falhou."
  exit 1
fi

echo "Build do Oryx concluído."
echo "--- Fim do Script de Deploy Personalizado ---"
