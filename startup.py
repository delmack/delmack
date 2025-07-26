import os
import sys

# Adiciona o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == "__main__":
    # Para Azure Web Apps, usa a porta fornecida pela variável de ambiente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

