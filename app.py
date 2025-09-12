from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'delmack_secret_key_2024'

# Configuração do banco de dados
def criar_banco_dados():
    conn = sqlite3.connect('delmack.db')
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        tipo TEXT NOT NULL,
        nome TEXT NOT NULL,
        email TEXT NOT NULL
    )
    ''')
    
    # Tabela de imóveis (simplificada)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imoveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        endereco TEXT NOT NULL,
        bairro TEXT NOT NULL,
        tipo TEXT NOT NULL,
        quartos INTEGER,
        valor DECIMAL,
        status TEXT NOT NULL,
        proprietario_nome TEXT
    )
    ''')
    
    # Inserir usuário admin padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'adm'")
    if cursor.fetchone()[0] == 0:
        senha_hash = hashlib.sha256('adm'.encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (username, password, tipo, nome, email) VALUES (?, ?, ?, ?, ?)",
                      ('adm', senha_hash, 'gerente', 'Administrador', 'admin@delmack.com'))
    
    # Inserir alguns imóveis de exemplo
    cursor.execute("SELECT COUNT(*) FROM imoveis")
    if cursor.fetchone()[0] == 0:
        imoveis_exemplo = [
            ('IMO001', 'Rua das Flores, 123', 'Jardim Paulista', 'Apartamento', 3, 750000.00, 'Ativo', 'Maria Santos'),
            ('IMO002', 'Av. Brasil, 456', 'Moema', 'Casa', 4, 1200000.00, 'Ativo', 'João Silva'),
            ('IMO003', 'Rua Augusta, 789', 'Consolação', 'Comercial', 0, 950000.00, 'Pendente', 'Empresa XYZ')
        ]
        
        for imovel in imoveis_exemplo:
            cursor.execute("INSERT INTO imoveis (codigo, endereco, bairro, tipo, quartos, valor, status, proprietario_nome) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", imovel)
    
    conn.commit()
    conn.close()

# Rotas da aplicação
@app.route('/')
def home():
    if 'usuario_logado' in session:
        return render_template('baggio.html', usuario=session['usuario_logado'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('delmack.db')
        cursor = conn.cursor()
        
        senha_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, senha_hash))
        usuario = cursor.fetchone()
        
        conn.close()
        
        if usuario:
            session['usuario_logado'] = {
                'id': usuario[0],
                'username': usuario[1],
                'tipo': usuario[3],
                'nome': usuario[4]
            }
            return jsonify({'success': True, 'message': 'Login realizado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Credenciais inválidas!'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    return redirect(url_for('login'))

@app.route('/api/imoveis')
def api_imoveis():
    if 'usuario_logado' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = sqlite3.connect('delmack.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT codigo, endereco, bairro, tipo, quartos, valor, status, proprietario_nome FROM imoveis ORDER BY id DESC")
    imoveis = cursor.fetchall()
    conn.close()
    
    # Converter para dicionário
    colunas = ['codigo', 'endereco', 'bairro', 'tipo', 'quartos', 'valor', 'status', 'proprietario_nome']
    imoveis_dict = [dict(zip(colunas, imovel)) for imovel in imoveis]
    
    return jsonify(imoveis_dict)

@app.route('/api/imovel', methods=['POST'])
def api_adicionar_imovel():
    if 'usuario_logado' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    dados = request.get_json()
    
    conn = sqlite3.connect('delmack.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO imoveis (codigo, endereco, bairro, tipo, quartos, valor, status, proprietario_nome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados['codigo'],
            dados['endereco'],
            dados['bairro'],
            dados['tipo'],
            dados['quartos'],
            dados['valor'],
            'Ativo',
            dados['proprietario_nome']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Imóvel cadastrado com sucesso!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao cadastrar imóvel: {str(e)}'})

if __name__ == '__main__':
    criar_banco_dados()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)