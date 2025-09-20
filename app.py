# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from database import init_db
import sqlite3

# --- Configuração Inicial ---
app = Flask(__name__)
app.config.from_object(Config)

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == "gerente@delmack.com" and password == "1234":
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos. Tente novamente.', 'danger')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    dados_dashboard = {
        'total_vendas_mes': 'R$ 1.250.000,00',
        'novos_leads': 42,
        'imoveis_angariados': 8,
        'taxa_conversao': '15%'
    }
    return render_template('dashboard.html', dados=dados_dashboard)

@app.route('/corretores')
def corretores():
    return render_template('corretores.html')

@app.route('/metas')
def metas():
    return render_template('metas.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

@app.route('/imoveis')
def imoveis():
    return render_template('imoveis.html')

@app.route('/importar', methods=['GET', 'POST'])
def importar():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'warning')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'warning')
            return redirect(request.url)
        if file:
            flash(f'Arquivo "{file.filename}" recebido com sucesso! A importação será processada.', 'success')
            return redirect(url_for('importar'))
            
    return render_template('importar.html')

@app.route('/logout')
def logout():
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# --- Execução da Aplicação ---
if __name__ == '__main__':
    init_db() 
    app.run(debug=True, host="0.0.0.0", port=5001)
