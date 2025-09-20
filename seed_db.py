# seed_db.py
import sqlite3
from datetime import datetime, timedelta
import random

# --- DADOS DE EXEMPLO ---

# Lista de usuários para criar
# Senha para todos (para teste): '1234' -> Em um sistema real, usaríamos hashes (bcrypt)
# A senha '1234' não será armazenada, apenas o seu hash.
# Para simplificar, vamos inserir a senha como texto plano por enquanto.
# ATENÇÃO: Em produção, isso é uma falha de segurança grave.
users_data = [
    # id=1
    ('Admin Delmack', 'admin@delmack.com', 'admin123', 'admin', None, 'N/A'),
    # id=2
    ('Gerente Carlos', 'gerente@delmack.com', '1234', 'gerente', None, '(11) 99999-0001'),
    # id=3
    ('Ana Silva', 'ana.silva@delmack.com', '1234', 'corretor', '12345-F', '(11) 98765-4321'),
    # id=4
    ('Bruno Costa', 'bruno.costa@delmack.com', '1234', 'corretor', '54321-F', '(21) 91234-5678'),
    # id=5
    ('Carla Dias', 'carla.dias@delmack.com', '1234', 'corretor', '67890-F', '(31) 95678-1234'),
    # id=6
    ('Proprietário João', 'joao.prop@email.com', '1234', 'proprietario', None, '(11) 91111-1111'),
    # id=7
    ('Proprietária Maria', 'maria.prop@email.com', '1234', 'proprietario', None, '(21) 92222-2222'),
]

# Lista de imóveis para criar
imoveis_data = [
    # id=1
    ('AP001', 'Apartamento Moderno no Itaim Bibi', 'ativo', 6, 3), # prop_id=6, corretor_id=3 (Ana)
    # id=2
    ('CA002', 'Casa com Piscina na Barra da Tijuca', 'ativo', 7, 4), # prop_id=7, corretor_id=4 (Bruno)
    # id=3
    ('AP003', 'Cobertura Duplex em Moema', 'vendido', 6, 3),
    # id=4
    ('TE004', 'Terreno Comercial em Alphaville', 'ativo', 7, 5), # prop_id=7, corretor_id=5 (Carla)
    # id=5
    ('AP005', 'Apartamento 2 Quartos em Copacabana', 'vendido', 6, 4),
]

# Lista de vendas para criar (dentro do último mês)
vendas_data = [
    # imovel_id, corretor_id, data_venda, valor_venda, comissao
    (3, 4, (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'), 1800000.00, 108000.00), # Bruno vendeu o imóvel 3
    (5, 3, (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), 950000.00, 57000.00),   # Ana vendeu o imóvel 5
]


def seed_database():
    """Função para limpar tabelas existentes e popular com dados de exemplo."""
    conn = sqlite3.connect('delmack.db')
    cursor = conn.cursor()

    print("Iniciando o processo de seeding...")

    # --- Limpando dados antigos para evitar duplicatas ---
    # A ordem é importante por causa das chaves estrangeiras (venda -> imovel -> user)
    print("Limpando tabelas existentes...")
    cursor.execute("DELETE FROM venda")
    cursor.execute("DELETE FROM imovel")
    cursor.execute("DELETE FROM user")
    # Reseta o autoincremento para começar do 1 novamente
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('venda', 'imovel', 'user')")
    
    # --- Inserindo Usuários ---
    print(f"Inserindo {len(users_data)} usuários...")
    cursor.executemany("INSERT INTO user (nome, email, password, role, creci, telefone) VALUES (?, ?, ?, ?, ?, ?)", users_data)

    # --- Inserindo Imóveis ---
    print(f"Inserindo {len(imoveis_data)} imóveis...")
    cursor.executemany("INSERT INTO imovel (codigo, titulo, status, proprietario_id, corretor_id) VALUES (?, ?, ?, ?, ?)", imoveis_data)

    # --- Inserindo Vendas ---
    print(f"Inserindo {len(vendas_data)} vendas...")
    cursor.executemany("INSERT INTO venda (imovel_id, corretor_id, data_venda, valor_venda, comissao) VALUES (?, ?, ?, ?, ?)", vendas_data)

    conn.commit()
    conn.close()

    print("\nBanco de dados populado com sucesso!")
    print(f"Total de {len(users_data)} usuários, {len(imoveis_data)} imóveis e {len(vendas_data)} vendas inseridas.")

if __name__ == '__main__':
    # Confirmação para evitar execução acidental
    confirm = input("ATENÇÃO: Isso irá apagar todos os dados existentes nas tabelas e inserir dados de exemplo. Deseja continuar? (s/n): ")
    if confirm.lower() == 's':
        seed_database()
    else:
        print("Operação cancelada.")
