
# app.py

# -----------------------------------------------------------------------------
# Portal de Dashboards para Baggio Imóveis - MVP
# Desenvolvido por: Delmack Consultoria
# Contato para Suporte: delmackconsultoria@gmail.com
# -----------------------------------------------------------------------------

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from jinja2 import BaseLoader, TemplateNotFound
from collections import Counter
import statistics

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-dificil-de-adivinhar'

# Banco de Dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'portal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Config API
app.config['PROPERFY_API_TOKEN'] = '05ad4b19-08e7-4534-a594-51e3665fe0f5'
app.config['PROPERFY_API_URL'] = 'https://sandbox.properfy.com.br/api/property/property'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos
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

# Loader customizado de templates
class DictLoader(BaseLoader):
    def __init__(self, templates):
        self.templates = templates
    
    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            return source, template, lambda: True
        raise TemplateNotFound(template)

# Dicionário de templates
html_templates = {
    "layout.html": """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Portal Baggio Imóveis{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        :root {
            --primary-blue: #0A1128;
            --secondary-orange: #FF7F11;
            --light-gray: #f8f9fa;
            --dark-text: #343a40;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light-gray);
            color: var(--dark-text);
        }
        .navbar {
            background-color: var(--primary-blue) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,.1);
        }
        .navbar-brand {
            display: flex;
            align-items: center;
            color: #fff !important;
            font-weight: bold;
        }
        .navbar-brand img {
            height: 40px;
            margin-right: 10px;
        }
        .nav-link {
            color: #fff !important;
            transition: color 0.3s ease;
        }
        .nav-link:hover {
            color: var(--secondary-orange) !important;
        }
        .container {
            padding: 30px 15px;
        }
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,.05);
            margin-bottom: 20px;
        }
        .card-header {
            background-color: var(--primary-blue);
            color: #fff;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-weight: bold;
        }
        .btn-primary {
            background-color: var(--secondary-orange);
            border-color: var(--secondary-orange);
            transition: background-color 0.3s ease;
        }
        .btn-primary:hover {
            background-color: #e66a00;
            border-color: #e66a00;
        }
        .badge-primary {
            background-color: var(--primary-blue) !important;
        }
        .badge-success {
            background-color: #28a745 !important;
        }
        .badge-warning {
            background-color: #ffc107 !important;
            color: #212529 !important;
        }
        .badge-danger {
            background-color: #dc3545 !important;
        }
        .table thead th {
            background-color: var(--primary-blue);
            color: #fff;
            border-bottom: none;
        }
        .table-striped tbody tr:nth-of-type(odd) {
            background-color: rgba(0, 0, 0, .03);
        }
        .form-control:focus {
            border-color: var(--secondary-orange);
            box-shadow: 0 0 0 0.25rem rgba(255, 127, 17, 0.25);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <img src="{{ url_for('static', filename='baggio-logo.png') }}" alt="Baggio Imóveis Logo">
                Baggio Imóveis
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/imoveis"><i class="fas fa-building me-1"></i>Imóveis</a></li>
                    <li class="nav-item"><a class="nav-link" href="/contratos"><i class="fas fa-file-contract me-1"></i>Contratos</a></li>
                    <li class="nav-item"><a class="nav-link" href="/graficos"><i class="fas fa-chart-bar me-1"></i>Gráficos</a></li>
                    <li class="nav-item"><a class="nav-link" href="/leads"><i class="fas fa-users me-1"></i>Leads</a></li>
                    <li class="nav-item"><a class="nav-link" href="/manutencao"><i class="fas fa-tools me-1"></i>Manutenção</a></li>
                    {% if current_user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt me-1"></i>Sair</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="/login"><i class="fas fa-sign-in-alt me-1"></i>Login</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
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
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
    """,

    "imoveis.html": """
{% extends "layout.html" %}
{% block title %}Imóveis{% endblock %}
{% block content %}
<div class="text-center">
    <h2 class="mb-4">Mapa de Imóveis</h2>
    <div id="mapa-imoveis" class="card card-body">
        <p>Mapa interativo dos imóveis disponíveis</p>
        <!-- Espaço reservado para o mapa -->
        <div style="height: 400px; background-color: #e9ecef; display: flex; align-items: center; justify-content: center;">
            Mapa será implementado aqui
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    console.log('Scripts para o mapa de imóveis carregados');
    // Implementação do mapa virá aqui
</script>
{% endblock %}
""",

    "contratos.html": """
{% extends "layout.html" %}
{% block title %}Contratos{% endblock %}
{% block content %}
<div class="text-center">
    <h2 class="mb-4">Contratos de Locação</h2>
    <div id="tabela-contratos" class="card card-body">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Cliente</th>
                    <th>Imóvel</th>
                    <th>Valor</th>
                    <th>Vencimento</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>João Silva</td>
                    <td>Apartamento 101</td>
                    <td>R$ 1.200,00</td>
                    <td>10/08/2023</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Maria Souza</td>
                    <td>Casa 205</td>
                    <td>R$ 1.800,00</td>
                    <td>15/08/2023</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
""",

    "graficos.html": """
{% extends "layout.html" %}
{% block title %}Gráficos de Imóveis{% endblock %}
{% block content %}
<div class="text-center">
    <h2 class="mb-4">Gráficos de Dados de Imóveis</h2>
    <div id="container-graficos" class="row">
        <div class="col-md-6">
            <div class="card mb-4">
                <div class="card-header">Distribuição de Imóveis</div>
                <div class="card-body">
                    <canvas id="grafico-tipos" height="300"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card mb-4">
                <div class="card-header">Valores de Aluguel</div>
                <div class="card-body">
                    <canvas id="grafico-valores" height="300"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Exemplo de gráfico - implementação real virá da API
    const ctx1 = document.getElementById('grafico-tipos').getContext('2d');
    new Chart(ctx1, {
        type: 'pie',
        data: {
            labels: ['Apartamentos', 'Casas', 'Comerciais', 'Terrenos'],
            datasets: [{
                data: [45, 30, 15, 10],
                backgroundColor: ['#0A1128', '#FF7F11', '#36b9cc', '#f6c23e']
            }]
        }
    });

    const ctx2 = document.getElementById('grafico-valores').getContext('2d');
    new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['< R$1000', 'R$1000-2000', 'R$2000-3000', '> R$3000'],
            datasets: [{
                label: 'Quantidade',
                data: [12, 19, 8, 5],
                backgroundColor: '#0A1128'
            }]
        }
    });
</script>
{% endblock %}
""",

    "leads.html": """
{% extends "layout.html" %}
{% block title %}Leads{% endblock %}
{% block content %}
<div class="text-center">
    <h2 class="mb-4">Análise de Leads</h2>
    <div id="leads-dashboard" class="card card-body">
        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="card border-left-primary shadow h-100 py-2">
                    <div class="card-body">
                        <div class="row no-gutters align-items-center">
                            <div class="col mr-2">
                                <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                    Leads Totais</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">128</div>
                            </div>
                            <div class="col-auto">
                                <i class="fas fa-users fa-2x text-gray-300"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="card border-left-success shadow h-100 py-2">
                    <div class="card-body">
                        <div class="row no-gutters align-items-center">
                            <div class="col mr-2">
                                <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                    Leads Convertidos</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">24</div>
                            </div>
                            <div class="col-auto">
                                <i class="fas fa-check-circle fa-2x text-gray-300"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="card border-left-info shadow h-100 py-2">
                    <div class="card-body">
                        <div class="row no-gutters align-items-center">
                            <div class="col mr-2">
                                <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                                    Taxa de Conversão</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">18.75%</div>
                            </div>
                            <div class="col-auto">
                                <i class="fas fa-percent fa-2x text-gray-300"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card shadow mb-4">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Últimos Leads</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Contato</th>
                                <th>Interesse</th>
                                <th>Data</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Carlos Oliveira</td>
                                <td>(11) 98765-4321</td>
                                <td>Apartamento 2 quartos</td>
                                <td>10/07/2023</td>
                                <td><span class="badge bg-warning text-dark">Em andamento</span></td>
                            </tr>
                            <tr>
                                <td>Ana Santos</td>
                                <td>(11) 91234-5678</td>
                                <td>Casa com jardim</td>
                                <td>08/07/2023</td>
                                <td><span class="badge bg-success">Convertido</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""",

    "manutencao.html": """
{% extends "layout.html" %}
{% block title %}Manutenção{% endblock %}
{% block content %}
<div class="text-center">
    <h2 class="mb-4">Painel de Manutenções</h2>
    <div id="painel-manutencao" class="card card-body">
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>Solicitações Pendentes</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Vazamento no apartamento 302
                                <span class="badge bg-danger">Urgente</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Troca de lâmpada na área comum
                                <span class="badge bg-warning text-dark">Normal</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Manutenções Concluídas</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Pintura do hall de entrada
                                <span class="badge bg-success">Concluído</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Reparo no portão eletrônico
                                <span class="badge bg-success">Concluído</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""",

    "login.html": """
{% extends "layout.html" %}
{% block title %}Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow-lg">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">Acesso ao Sistema</h4>
            </div>
            <div class="card-body">
                <form method="POST" action="/login">
                    <div class="mb-3">
                        <label for="username" class="form-label">Usuário</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Senha</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Entrar</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
}

# Carrega os templates
app.jinja_loader = DictLoader(html_templates)

# User loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorador para verificar se o usuário é super admin
def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash('Acesso restrito a super administradores.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas básicas
@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/imoveis')
@login_required
def imoveis():
    return render_template('imoveis.html')

@app.route('/contratos')
@login_required
def contratos():
    return render_template('contratos.html')

@app.route('/graficos')
@login_required
def graficos():
    return render_template('graficos.html')

@app.route('/leads')
@login_required
def leads():
    return render_template('leads.html')

@app.route('/manutencao')
@login_required
def manutencao():
    return render_template('manutencao.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# Rotas de administração (apenas para super admin)
@app.route('/admin')
@super_admin_required
def admin_panel():
    users = User.query.all()
    companies = Company.query.all()
    profiles = Profile.query.all()
    return render_template('admin.html', users=users, companies=companies, profiles=profiles)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@super_admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_super_admin = 'is_super_admin' in request.form
        company_id = request.form.get('company_id')
        profile_id = request.form.get('profile_id')

        if not username or not email or not password:
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('add_user'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password,
                        is_super_admin=is_super_admin, company_id=company_id, profile_id=profile_id)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário adicionado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    companies = Company.query.all()
    profiles = Profile.query.all()
    return render_template('add_user.html', companies=companies, profiles=profiles)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@super_admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.is_super_admin = 'is_super_admin' in request.form
        user.company_id = request.form.get('company_id')
        user.profile_id = request.form.get('profile_id')
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    companies = Company.query.all()
    profiles = Profile.query.all()
    return render_template('edit_user.html', user=user, companies=companies, profiles=profiles)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/companies/add', methods=['GET', 'POST'])
@super_admin_required
def add_company():
    if request.method == 'POST':
        name = request.form.get('name')
        new_company = Company(name=name)
        db.session.add(new_company)
        db.session.commit()
        flash('Empresa adicionada com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('add_company.html')

@app.route('/admin/companies/edit/<int:company_id>', methods=['GET', 'POST'])
@super_admin_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    if request.method == 'POST':
        company.name = request.form.get('name')
        db.session.commit()
        flash('Empresa atualizada com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('edit_company.html', company=company)

@app.route('/admin/companies/delete/<int:company_id>', methods=['POST'])
@super_admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Empresa excluída com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/profiles/add', methods=['GET', 'POST'])
@super_admin_required
def add_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        report_url = request.form.get('report_url')
        new_profile = Profile(name=name, report_url=report_url)
        db.session.add(new_profile)
        db.session.commit()
        flash('Perfil adicionado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('add_profile.html')

@app.route('/admin/profiles/edit/<int:profile_id>', methods=['GET', 'POST'])
@super_admin_required
def edit_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if request.method == 'POST':
        profile.name = request.form.get('name')
        profile.report_url = request.form.get('report_url')
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('edit_profile.html', profile=profile)

@app.route('/admin/profiles/delete/<int:profile_id>', methods=['POST'])
@super_admin_required
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    db.session.delete(profile)
    db.session.commit()
    flash('Perfil excluído com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

# Rotas da API Properfy
@app.route('/api/properties', methods=['GET'])
@login_required
def get_properties():
    token = app.config['PROPERFY_API_TOKEN']
    api_url = app.config['PROPERFY_API_URL']
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# Inicialização do banco de dados
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Exemplo de criação de usuário super admin se não existir
        if not User.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('adminpass', method='pbkdf2:sha256')
            admin_user = User(username='admin', email='admin@example.com', password_hash=hashed_password, is_super_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário 'admin' criado com sucesso.")

    # Para Azure Web Apps, usa a porta fornecida pela variável de ambiente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


