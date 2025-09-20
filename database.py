# database.py
import sqlite3

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect('delmack.db')
    cursor = conn.cursor()

    # Tabela de Usuários (Corretores, Gerentes, etc.)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'gerente', 'corretor', 'proprietario')),
        creci TEXT,
        telefone TEXT
    )
    ''')

    # Tabela de Imóveis
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imovel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        titulo TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('ativo', 'vendido', 'inativo')),
        proprietario_id INTEGER,
        corretor_id INTEGER, -- Corretor que angariou
        FOREIGN KEY (proprietario_id) REFERENCES user (id),
        FOREIGN KEY (corretor_id) REFERENCES user (id)
    )
    ''')
    
    # Tabela de Vendas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imovel_id INTEGER NOT NULL,
        corretor_id INTEGER NOT NULL, -- Corretor que vendeu
        data_venda DATE NOT NULL,
        valor_venda REAL NOT NULL,
        comissao REAL NOT NULL,
        FOREIGN KEY (imovel_id) REFERENCES imovel (id),
        FOREIGN KEY (corretor_id) REFERENCES user (id)
    )
    ''')

    print("Banco de dados inicializado com sucesso.")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
