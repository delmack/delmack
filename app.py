# -----------------------------------------------------------------------------
# Portal de Dashboards para Baggio Imóveis - MVP
# Desenvolvido por: Delmack Consultoria
# Contato para Suporte: delmackconsultoria@gmail.com
#
# Instruções de Uso:
# 1. Salve este código como 'app.py'.
# 2. Instale as dependências necessárias: 
#    pip install -r requirements.txt
# 3. Execute o script no terminal: python app.py
# 4. O primeiro usuário a se cadastrar será o Super Admin.
# -----------------------------------------------------------------------------

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from jinja2 import BaseLoader, TemplateNotFound
from io import StringIO
from collections import Counter
import statistics
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-muito-forte-e-dificil-de-adivinhar')

# Configuração do Banco de Dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'portal.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração da API Properfy
app.config['PROPERFY_API_TOKEN'] = os.getenv('PROPERFY_API_TOKEN', '05ad4b19-08e7-4534-a594-51e3665fe0f5')
app.config['PROPERFY_API_URL'] = 'https://sandbox.properfy.com.br/api/property/property'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# --- MODELOS DO BANCO DE DADOS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    company = db.relationship('Company', backref=db.backref('users', lazy=True))
    profile = db.relationship('Profile', backref=db.backref('users', lazy=True))

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    report_url = db.Column(db.String(500), nullable=True)

# --- LOADER DE TEMPLATES EM MEMÓRIA ---
class DictLoader(BaseLoader):
    def __init__(self, templates):
        self.templates = templates

    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            return source, template, lambda: True
        raise TemplateNotFound(template)

# --- TEMPLATES EM MEMÓRIA ---
html_templates = {
    "layout.html": """
<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{% endblock %} - Baggio Imóveis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
      :root {
        --primary-blue: #1a365d;
        --secondary-blue: #2c5282;
        --accent-orange: #ed8936;
        --light-orange: #fbd38d;
        --dark-gray: #2d3748;
        --light-gray: #e2e8f0;
      }
      
      body { 
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      
      .navbar { 
        background-color: var(--primary-blue) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      
      .navbar-brand {
        font-weight: 700;
        color: white !important;
      }
      
      .nav-link {
        color: rgba(255,255,255,0.8) !important;
        font-weight: 500;
        transition: all 0.3s;
      }
      
      .nav-link:hover, .nav-link.active {
        color: var(--accent-orange) !important;
      }
      
      .btn-primary {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
      }
      
      .btn-primary:hover {
        background-color: var(--secondary-blue);
        border-color: var(--secondary-blue);
      }
      
      .btn-accent {
        background-color: var(--accent-orange);
        border-color: var(--accent-orange);
        color: white;
      }
      
      .btn-accent:hover {
        background-color: #dd6b20;
        border-color: #dd6b20;
      }
      
      .footer { 
        background-color: var(--primary-blue);
        color: white;
        padding: 20px 0;
        margin-top: 40px;
      }
      
      .card { 
        margin-bottom: 1.5rem; 
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.3s, box-shadow 0.3s;
        border: none;
      }
      
      .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
      }
      
      .card-header {
        background-color: var(--primary-blue);
        color: white;
        border-radius: 10px 10px 0 0 !important;
      }
      
      .iframe-container { 
        position: relative; 
        overflow: hidden; 
        width: 100%; 
        padding-top: 56.25%; 
        border-radius: 10px;
      }
      
      .responsive-iframe { 
        position: absolute; 
        top: 0; 
        left: 0; 
        bottom: 0; 
        right: 0; 
        width: 100%; 
        height: 100%; 
        border-radius: 10px;
      }
      
      .auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }
      
      .logo-container {
        text-align: center;
        margin-bottom: 2rem;
      }
      
      .logo-img {
        max-height: 100px;
        margin-bottom: 1rem;
      }
    </style>
    {% block extra_css %}{% endblock %}
  </head>
  <body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
      <div class="container">
        <a class="navbar-brand d-flex align-items-center" href="{{ url_for('index') }}">
          <img src="{{ url_for('static', filename='baggio-logo.png') }}" alt="Baggio Imóveis" height="40" class="me-2">
          Portal Baggio
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            {% if current_user.is_authenticated %}
              {% if current_user.is_super_admin %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_dashboard') }}"><i class="bi bi-speedometer2 me-1"></i> Admin</a></li>
              {% else %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}"><i class="bi bi-speedometer2 me-1"></i> Dashboard</a></li>
              {% endif %}
              <li class="nav-item"><a class="nav-link" href="{{ url_for('imoveis') }}"><i class="bi bi-house me-1"></i> Imóveis</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('contratos') }}"><i class="bi bi-file-earmark-text me-1"></i> Contratos</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('graficos') }}"><i class="bi bi-bar-chart me-1"></i> Gráficos</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('leads') }}"><i class="bi bi-people me-1"></i> Leads</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('manutencao') }}"><i class="bi bi-tools me-1"></i> Manutenção</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}"><i class="bi bi-box-arrow-right me-1"></i> Sair</a></li>
            {% else %}
              <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}"><i class="bi bi-box-arrow-in-right me-1"></i> Login</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('register') }}"><i class="bi bi-person-plus me-1"></i> Cadastrar</a></li>
            {% endif %}
          </ul>
        </div>
      </div>
    </nav>

    <main class="container">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
              {{ message }}
              <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      {% block content %}{% endblock %}
    </main>

    <footer class="footer mt-5">
      <div class="container text-center">
        <span>© 2023 Baggio Imóveis - Todos os direitos reservados</span>
        <div class="mt-2">
          <small>Desenvolvido por: <strong>Delmack Consultoria</strong> | Contato: <a href="mailto:delmackconsultoria@gmail.com" class="text-white">delmackconsultoria@gmail.com</a></small>
        </div>
      </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
  </body>
</html>
    """,
    "index.html": """
{% extends "layout.html" %}
{% block title %}Bem-vindo - Baggio Imóveis{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <div class="card border-0 shadow-lg">
      <div class="card-body text-center p-5">
        <img src="{{ url_for('static', filename='baggio-logo.png') }}" alt="Baggio Imóveis" class="img-fluid mb-4" style="max-height: 120px;">
        <h1 class="display-5 fw-bold mb-4">Portal de Dashboards Baggio Imóveis</h1>
        <p class="lead mb-4">Acesse seus relatórios de Business Intelligence de forma centralizada e segura.</p>
        <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
          <a href="{{ url_for('login') }}" class="btn btn-accent btn-lg px-4 gap-3">Fazer Login</a>
          <a href="{{ url_for('register') }}" class="btn btn-outline-secondary btn-lg px-4">Cadastrar</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
    """,
    "login.html": """
{% extends "layout.html" %}
{% block title %}Login - Baggio Imóveis{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="auth-container">
      <div class="logo-container">
        <img src="{{ url_for('static', filename='baggio-logo.png') }}" alt="Baggio Imóveis" class="logo-img">
        <h3 class="text-center">Acesse o Portal</h3>
      </div>
      
      <form method="POST" action="{{ url_for('login') }}">
        <div class="mb-3">
          <label for="email" class="form-label">E-mail</label>
          <input type="email" class="form-control" id="email" name="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Senha</label>
          <input type="password" class="form-control" id="password" name="password" required>
        </div>
        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-accent">Entrar</button>
          <a href="{{ url_for('register') }}" class="btn btn-outline-secondary">Criar conta</a>
        </div>
        <div class="text-center mt-3">
          <a href="#" class="text-muted">Esqueceu sua senha?</a>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}
    """,
    "register.html": """
{% extends "layout.html" %}
{% block title %}Cadastro - Baggio Imóveis{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="auth-container">
      <div class="logo-container">
        <img src="{{ url_for('static', filename='baggio-logo.png') }}" alt="Baggio Imóveis" class="logo-img">
        <h3 class="text-center">Criar Nova Conta</h3>
      </div>
      
      <form method="POST" action="{{ url_for('register') }}">
        <div class="mb-3">
          <label for="username" class="form-label">Nome de Usuário</label>
          <input type="text" class="form-control" id="username" name="username" required>
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">E-mail</label>
          <input type="email" class="form-control" id="email" name="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Senha</label>
          <input type="password" class="form-control" id="password" name="password" required>
        </div>
        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-accent">Cadastrar</button>
          <a href="{{ url_for('login') }}" class="btn btn-outline-secondary">Já tenho uma conta</a>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}
    """,
    "dashboard.html": """
{% extends "layout.html" %}
{% block title %}Dashboard - Baggio Imóveis{% endblock %}
{% block content %}
  <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h2 class="h2">Seu Dashboard</h2>
  </div>
  
  <div class="card">
    <div class="card-header">
      <h5 class="card-title mb-0">Relatório de Performance</h5>
    </div>
    <div class="card-body">
      <div class="iframe-container">
        <iframe title="Relatório" class="responsive-iframe" src="{{ report_url }}" frameborder="0" allowFullScreen="true"></iframe>
      </div>
    </div>
  </div>
{% endblock %}
    """,
    "dashboard_no_access.html": """
{% extends "layout.html" %}
{% block title %}Acesso Negado - Baggio Imóveis{% endblock %}
{% block content %}
<div class="alert alert-warning">
  <div class="d-flex align-items-center">
    <i class="bi bi-exclamation-triangle-fill me-3" style="font-size: 2rem;"></i>
    <div>
      <h4 class="alert-heading">Acesso Pendente</h4>
      <p>Você ainda não foi associado a um perfil de visualização. Por favor, entre em contato com o administrador do sistema para que ele configure seu acesso.</p>
      <a href="{{ url_for('logout') }}" class="btn btn-sm btn-outline-secondary">Sair</a>
    </div>
  </div>
</div>
{% endblock %}
    """,
    # ... (mantenha os outros templates originais, mas adicione as classes de estilo conforme o layout.html)
}

# Configura o loader de templates personalizado
app.jinja_loader = DictLoader(html_templates)

# --- FUNÇÕES AUXILIARES E DECORATORS ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login falhou. Verifique seu e-mail e senha.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Verifica se já existe
        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'warning')
            return redirect(url_for('register'))

        # O primeiro usuário a se registrar se torna Super Admin
        is_first_user = User.query.count() == 0
       
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            is_super_admin=is_first_user
        )
        db.session.add(new_user)
        db.session.commit()
       
        flash('Conta criada com sucesso! Você já pode fazer login.', 'success')
        if is_first_user:
            flash('Parabéns! Você é o primeiro usuário e foi definido como Super Administrador.', 'info')
           
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_super_admin:
        return redirect(url_for('admin_dashboard'))
   
    if not current_user.profile or not current_user.profile.report_url:
        return render_template('dashboard_no_access.html')
       
    report_url = current_user.profile.report_url
    return render_template('dashboard.html', report_url=report_url)

# --- ROTA DO MAPA DE IMÓVEIS ---
@app.route('/imoveis')
@login_required
def imoveis():
    return render_template('imoveis.html')

@app.route('/api/imoveis')
@login_required
def api_imoveis():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        params = {'page': 1, 'size': 3000}
        
        response = requests.get(
            app.config['PROPERFY_API_URL'],
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        imoveis = []
        for item in response.json().get('data', []):
            if (item.get('dcmAddressLatitude') is not None and 
                item.get('dcmAddressLongitude') is not None and
                item.get('chrCondoName') is not None):
                imoveis.append({
                    'id': item.get('id'),
                    'chrCondoName': item['chrCondoName'],
                    'chrType': item.get('chrType', 'Não informado'),
                    'chrAddressStreet': item.get('chrAddressStreet', 'Não informado'),
                    'chrAddressPostalCode': item.get('chrAddressPostalCode', 'Não informado'),
                    'chrAddressDistrict': item.get('chrAddressDistrict', 'Não informado'),
                    'chrTransactionType': item.get('chrTransactionType'),
                    'dcmSale': item.get('dcmSale'),
                    'dcmExpectedRent': item.get('dcmExpectedRent'),
                    'dcmCondoValue': item.get('dcmCondoValue'),
                    'dcmAddressLatitude': float(item['dcmAddressLatitude']),
                    'dcmAddressLongitude': float(item['dcmAddressLongitude'])
                })
        
        return jsonify(imoveis)
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição à API Properfy: {str(e)}")
        return jsonify({'error': 'Erro ao buscar dados da API'}), 500
    except Exception as e:
        app.logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({'error': 'Erro interno no servidor'}), 500

@app.route('/api/imoveis/graficos')
@login_required
def api_imoveis_graficos():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        params = {'page': 1, 'size': 3000}
        
        response = requests.get(
            app.config['PROPERFY_API_URL'],
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        properties_data = response.json().get('data', [])
        
        transacoes = Counter([p.get('chrTransactionType', 'N/A') for p in properties_data])
        tipos = Counter([p.get('chrType', 'N/A') for p in properties_data])
        propositos = Counter([p.get('chrPurpose', 'N/A') for p in properties_data])

        return jsonify({
            'transacao': {'labels': list(transacoes.keys()), 'values': list(transacoes.values())},
            'tipo': {'labels': list(tipos.keys()), 'values': list(tipos.values())},
            'proposito': {'labels': list(propositos.keys()), 'values': list(propositos.values())}
        })

    except Exception as e:
        app.logger.error(f"Erro ao gerar dados para gráficos do mapa: {e}")
        return jsonify({'error': 'Erro ao gerar dados para gráficos'}), 500

# --- ROTA PARA CONTRATOS ---
@app.route('/contratos')
@login_required
def contratos():
    return render_template('contratos.html')

@app.route('/api/contratos')
@login_required
def api_contratos():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        app.logger.info("Iniciando busca de contratos de aluguel...")
        response = requests.get(
            'https://sandbox.properfy.com.br/api/rental/contract',
            headers=headers
        )
        response.raise_for_status()
        app.logger.info("Busca de contratos concluída com sucesso.")
        
        contracts_data = response.json()
        
        if isinstance(contracts_data, list):
            contracts = contracts_data
        elif isinstance(contracts_data, dict) and 'data' in contracts_data:
            contracts = contracts_data['data']
        else:
            contracts = []
        
        processed_contracts = []
        for contract in contracts:
            processed_contract = {
                'id': contract.get('id'),
                'tenant_name': contract.get('tenant_name') or contract.get('tenantName') or contract.get('chrTenantName'),
                'property_name': contract.get('property_name') or contract.get('propertyName') or contract.get('chrPropertyName'),
                'property_address': contract.get('property_address') or contract.get('propertyAddress') or contract.get('chrPropertyAddress'),
                'rent_value': contract.get('rent_value') or contract.get('rentValue') or contract.get('dcmRentValue') or 0,
                'start_date': contract.get('start_date') or contract.get('startDate') or contract.get('dtmStartDate'),
                'end_date': contract.get('end_date') or contract.get('endDate') or contract.get('dtmEndDate'),
                'status': contract.get('status') or contract.get('chrStatus'),
                'observations': contract.get('observations') or contract.get('chrObservations')
            }
            processed_contracts.append(processed_contract)
        
        app.logger.info(f"Processados {len(processed_contracts)} contratos.")
        return jsonify(processed_contracts)
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição à API de contratos: {e}")
        return jsonify({'error': 'Erro ao buscar dados da API de contratos'}), 500
    except Exception as e:
        app.logger.error(f"Erro inesperado na api_contratos: {e}")
        return jsonify({'error': 'Erro interno no servidor ao processar contratos'}), 500

# --- ROTA PARA GRÁFICOS ---
@app.route('/graficos')
@login_required
def graficos():
    return render_template('graficos.html')

@app.route('/api/graficos')
@login_required
def api_graficos():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        app.logger.info("Iniciando busca de dados para gráficos...")
        params = {'page': 1, 'size': 3000}
        response = requests.get(
            app.config['PROPERFY_API_URL'],
            headers=headers,
            params=params
        )
        response.raise_for_status()
        app.logger.info("Busca de dados para gráficos concluída com sucesso.")
        
        properties_data = response.json().get('data', [])
        
        processed_data = {
            'statistics': {},
            'charts': {}
        }
        
        tipos = []
        condicoes = []
        garagens = []
        anos = []
        valores = []
        areas = []
        
        for prop in properties_data:
            tipo = prop.get('chrType')
            if tipo:
                tipos.append(tipo)
            
            condicao = prop.get('chrCondition')
            if condicao:
                condicoes.append(condicao)
            
            garage = prop.get('intGarage')
            if garage is not None:
                garagens.append(garage)
            
            ano = prop.get('intBuiltYear')
            if ano and ano > 1900:
                anos.append(ano)
            
            valor = prop.get('dcmSale')
            if valor and valor > 0:
                valores.append(valor)
            
            area = prop.get('dcmAreaPrivate')
            if area and area > 0:
                areas.append(area)
        
        processed_data['statistics'] = {
            'total_imoveis': len(properties_data),
            'valor_medio': statistics.mean(valores) if valores else 0,
            'area_media': statistics.mean(areas) if areas else 0,
            'ano_medio': statistics.mean(anos) if anos else 0
        }
        
        if tipos:
            tipos_count = Counter(tipos)
            processed_data['charts']['tipos'] = {
                'labels': list(tipos_count.keys()),
                'values': list(tipos_count.values())
            }
        
        if condicoes:
            condicoes_count = Counter(condicoes)
            processed_data['charts']['condicoes'] = {
                'labels': list(condicoes_count.keys()),
                'values': list(condicoes_count.values())
            }
        
        if garagens:
            garagens_count = Counter(garagens)
            garagens_sorted = sorted(garagens_count.items())
            processed_data['charts']['garagens'] = {
                'labels': [f"{g} vagas" if g != 1 else "1 vaga" for g, _ in garagens_sorted],
                'values': [count for _, count in garagens_sorted]
            }
        
        if anos:
            decadas = {}
            for ano in anos:
                decada = (ano // 10) * 10
                decadas[decada] = decadas.get(decada, 0) + 1
            
            decadas_sorted = sorted(decadas.items())
            processed_data['charts']['decadas'] = {
                'labels': [f"{d}s" for d, _ in decadas_sorted],
                'values': [count for _, count in decadas_sorted]
            }
        
        if valores:
            faixas = {
                'Até R$ 100k': 0,
                'R$ 100k - 300k': 0,
                'R$ 300k - 500k': 0,
                'R$ 500k - 1M': 0,
                'Acima de R$ 1M': 0
            }
            
            for valor in valores:
                if valor <= 100000:
                    faixas['Até R$ 100k'] += 1
                elif valor <= 300000:
                    faixas['R$ 100k - 300k'] += 1
                elif valor <= 500000:
                    faixas['R$ 300k - 500k'] += 1
                elif valor <= 1000000:
                    faixas['R$ 500k - 1M'] += 1
                else:
                    faixas['Acima de R$ 1M'] += 1
            
            processed_data['charts']['valores'] = {
                'labels': list(faixas.keys()),
                'values': list(faixas.values())
            }
        
        if areas and valores:
            area_valor_data = []
            for prop in properties_data:
                area = prop.get('dcmAreaPrivate')
                valor = prop.get('dcmSale')
                if area and area > 0 and valor and valor > 0:
                    area_valor_data.append({'x': area, 'y': valor})
            
            processed_data['charts']['area_valor'] = area_valor_data
        
        app.logger.info(f"Processados dados de {len(properties_data)} imóveis para gráficos.")
        return jsonify(processed_data)
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição à API para gráficos: {e}")
        return jsonify({'error': 'Erro ao buscar dados da API para gráficos'}), 500
    except Exception as e:
        app.logger.error(f"Erro inesperado na api_graficos: {e}")
        return jsonify({'error': 'Erro interno no servidor ao processar dados para gráficos'}), 500

# --- ROTA PARA LEADS ---
@app.route('/leads')
@login_required
def leads():
    return render_template('leads.html')

@app.route('/api/leads')
@login_required
def api_leads():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        app.logger.info("Iniciando busca de dados de Leads...")
        
        lead_response = requests.get(
            'https://sandbox.properfy.com.br/api/crm/lead?filter=&size=3000',
            headers=headers
        )
        lead_response.raise_for_status()
        lead_data = lead_response.json().get('data', [])
        
        card_response = requests.get(
            'https://sandbox.properfy.com.br/api/crm/card',
            headers=headers
        )
        card_response.raise_for_status()
        card_data = card_response.json()
        
        lead_input_response = requests.get(
            'https://sandbox.properfy.com.br/api/crm/lead-input',
            headers=headers
        )
        lead_input_response.raise_for_status()
        lead_input_data = lead_input_response.json()

        app.logger.info("Busca de dados de Leads concluída com sucesso.")
        
        processed_data = {
            'statistics': {},
            'charts': {}
        }
        
        canais = [lead.get('chrAcquisitionChannel') for lead in lead_data if lead.get('chrAcquisitionChannel')]
        canais_count = Counter(canais)
        processed_data['charts']['canais'] = {
            'labels': list(canais_count.keys()),
            'values': list(canais_count.values())
        }
        
        status_cards = [card.get('chrStatus') for card in card_data if card.get('chrStatus')]
        status_cards_count = Counter(status_cards)
        processed_data['charts']['status_cards'] = {
            'labels': list(status_cards_count.keys()),
            'values': list(status_cards_count.values())
        }
        
        transacoes = [item.get('chrTransactionType') for item in lead_input_data if item.get('chrTransactionType')]
        transacoes_count = Counter(transacoes)
        processed_data['charts']['transacoes'] = {
            'labels': list(transacoes_count.keys()),
            'values': list(transacoes_count.values())
        }
        
        pipelines = [item.get('chrPipeline') for item in lead_input_data if item.get('chrPipeline')]
        pipelines_count = Counter(pipelines)
        processed_data['charts']['pipeline'] = {
            'labels': list(pipelines_count.keys()),
            'values': list(pipelines_count.values())
        }
        
        total_leads = len(lead_data)
        total_cards = len(card_data)
        cards_concluidos = status_cards.count('Concluído') + status_cards.count('Finalizado')
        taxa_conversao = (cards_concluidos / total_cards * 100) if total_cards > 0 else 0
        
        processed_data['statistics'] = {
            'total_leads': total_leads,
            'total_cards': total_cards,
            'cards_concluidos': cards_concluidos,
            'taxa_conversao': taxa_conversao
        }
        
        app.logger.info(f"Processados dados de {total_leads} leads e {total_cards} cards.")
        return jsonify(processed_data)
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição a uma das APIs de Leads: {e}")
        return jsonify({'error': 'Erro ao buscar dados de Leads'}), 500
    except Exception as e:
        app.logger.error(f"Erro inesperado na api_leads: {e}")
        return jsonify({'error': 'Erro interno no servidor ao processar dados de Leads'}), 500

# --- ROTA PARA MANUTENÇÃO ---
@app.route('/manutencao')
@login_required
def manutencao():
    return render_template('manutencao.html')

@app.route('/api/manutencao_graficos')
@login_required
def api_manutencao_graficos():
    try:
        headers = {
            'Authorization': f'Bearer {app.config["PROPERFY_API_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        app.logger.info("Iniciando busca de dados de Manutenção...")
        
        response = requests.get(
            'https://sandbox.properfy.com.br/api/property/maintenance/',
            headers=headers
        )
        response.raise_for_status()
        maintenance_data = response.json()
        
        if isinstance(maintenance_data, list):
            manutencoes = maintenance_data
        elif isinstance(maintenance_data, dict) and 'data' in maintenance_data:
            manutencoes = maintenance_data['data']
        else:
            manutencoes = []

        app.logger.info("Busca de dados de Manutenção concluída com sucesso.")
        
        processed_data = {
            'statistics': {},
            'charts': {}
        }
        
        prioridades = [item.get('chrPriority') for item in manutencoes if item.get('chrPriority')]
        prioridades_count = Counter(prioridades)
        processed_data['charts']['prioridades'] = {
            'labels': list(prioridades_count.keys()),
            'values': list(prioridades_count.values())
        }
        
        status = [item.get('chrStatus') for item in manutencoes if item.get('chrStatus')]
        status_count = Counter(status)
        processed_data['charts']['status'] = {
            'labels': list(status_count.keys()),
            'values': list(status_count.values())
        }
        
        responsaveis = [item.get('responsible') for item in manutencoes if item.get('responsible')]
        responsaveis_count = Counter(responsaveis)
        processed_data['charts']['responsaveis'] = {
            'labels': list(responsaveis_count.keys()),
            'values': list(responsaveis_count.values())
        }
        
        categorias = [item.get('chrCategoryLabel') for item in manutencoes if item.get('chrCategoryLabel')]
        categorias_count = Counter(categorias)
        processed_data['charts']['categorias'] = {
            'labels': list(categorias_count.keys()),
            'values': list(categorias_count.values())
        }
        
        total_manutencoes = len(manutencoes)
        alta_prioridade = prioridades.count('Alta') + prioridades.count('ALTA') + prioridades.count('alta')
        pendentes = status.count('Pendente') + status.count('PENDENTE') + status.count('pendente')
        concluidas = status.count('Concluído') + status.count('CONCLUÍDO') + status.count('concluído') + status.count('Finalizado') + status.count('FINALIZADO') + status.count('finalizado')
        
        processed_data['statistics'] = {
            'total_manutencoes': total_manutencoes,
            'alta_prioridade': alta_prioridade,
            'pendentes': pendentes,
            'concluidas': concluidas
        }
        
        app.logger.info(f"Processados dados de {total_manutencoes} manutenções.")
        return jsonify(processed_data)
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição à API de Manutenção: {e}")
        return jsonify({'error': 'Erro ao buscar dados de Manutenção'}), 500
    except Exception as e:
        app.logger.error(f"Erro inesperado na api_manutencao_graficos: {e}")
        return jsonify({'error': 'Erro interno no servidor ao processar dados de Manutenção'}), 500

# --- ROTAS DO SUPER ADMIN ---
@app.route('/admin')
@login_required
@super_admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_companies': Company.query.count(),
        'total_profiles': Profile.query.count()
    }
    return render_template('admin/admin_dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
@super_admin_required
def admin_users():
    users = User.query.all()
    companies = Company.query.all()
    profiles = Profile.query.all()
    return render_template('admin/admin_users.html', users=users, companies=companies, profiles=profiles)

@app.route('/admin/user/update/<int:user_id>', methods=['POST'])
@login_required
@super_admin_required
def admin_update_user(user_id):
    user = User.query.get_or_404(user_id)
    user.company_id = request.form.get('company_id') if request.form.get('company_id') else None
    user.profile_id = request.form.get('profile_id') if request.form.get('profile_id') else None
    db.session.commit()
    flash(f'Usuário {user.username} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_users'))
   
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@super_admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_super_admin:
        flash('Não é possível deletar a conta do Super Admin.', 'danger')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário {user.username} deletado com sucesso!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/companies', methods=['GET', 'POST'])
@login_required
@super_admin_required
def admin_companies():
    if request.method == 'POST':
        name = request.form.get('name')
        if not Company.query.filter_by(name=name).first():
            new_company = Company(name=name)
            db.session.add(new_company)
            db.session.commit()
            flash('Empresa adicionada com sucesso!', 'success')
        else:
            flash('Uma empresa com este nome já existe.', 'warning')
    companies = Company.query.all()
    return render_template('admin/admin_companies.html', companies=companies)

@app.route('/admin/profiles', methods=['GET', 'POST'])
@login_required
@super_admin_required
def admin_profiles():
    if request.method == 'POST':
        name = request.form.get('name')
        report_url = request.form.get('report_url')
        new_profile = Profile(name=name, report_url=report_url)
        db.session.add(new_profile)
        db.session.commit()
        flash('Perfil adicionado com sucesso!', 'success')
    profiles = Profile.query.all()
    return render_template('admin/admin_profiles.html', profiles=profiles)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)