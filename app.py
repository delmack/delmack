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
    <style>
        .navbar { margin-bottom: 20px; }
        .container { padding: 20px; }
        #mapa-imoveis, #tabela-contratos, #container-graficos, 
        #leads-dashboard, #painel-manutencao { 
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">Baggio Imóveis</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link" href="/imoveis">Imóveis</a></li>
                    <li class="nav-item"><a class="nav-link" href="/contratos">Contratos</a></li>
                    <li class="nav-item"><a class="nav-link" href="/graficos">Gráficos</a></li>
                    <li class="nav-item"><a class="nav-link" href="/leads">Leads</a></li>
                    <li class="nav-item"><a class="nav-link" href="/manutencao">Manutenção</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
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
    <div id="mapa-imoveis">
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
    <div id="tabela-contratos">
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
                backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e']
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
                backgroundColor: '#4e73df'
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
    <div id="leads-dashboard">
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
    <div id="painel-manutencao">
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

# Rotas básicas
@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/imoveis')
def imoveis():
    return render_template('imoveis.html')

@app.route('/contratos')
def contratos():
    return render_template('contratos.html')

@app.route('/graficos')
def graficos():
    return render_template('graficos.html')

@app.route('/leads')
def leads():
    return render_template('leads.html')

@app.route('/manutencao')
def manutencao():
    return render_template('manutencao.html')

# Sistema de login (básico)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# Função para criar usuário admin inicial (executar apenas uma vez)
def create_admin_user():
    with app.app_context():
        db.create_all()
        
        # Verifica se já existe um admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Cria empresa padrão
            company = Company(name='Baggio Imóveis')
            db.session.add(company)
            db.session.commit()
            
            # Cria perfil admin
            profile = Profile(name='Administrador')
            db.session.add(profile)
            db.session.commit()
            
            # Cria usuário admin
            hashed_password = generate_password_hash('admin123', method='sha256')
            admin_user = User(
                username='admin',
                email='admin@baggioimoveis.com',
                password_hash=hashed_password,
                is_super_admin=True,
                company_id=company.id,
                profile_id=profile.id
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Usuário admin criado com sucesso!')

if __name__ == '__main__':
    create_admin_user()
    app.run(debug=True)