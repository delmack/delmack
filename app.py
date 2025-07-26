# -----------------------------------------------------------------------------
# Portal de Dashboards para Imobiliárias - MVP
# Desenvolvido por: Delmack Consultoria
# Contato para Suporte: delmackconsultoria@gmail.com
#
# Instruções de Uso:
# 1. Salve este código como 'app.py'.
# 2. Instale as dependências necessárias: 
#    pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug requests
# 3. Execute o script no terminal: python app.py
# 4. Acesse em seu navegador: http://127.0.0.1:5000
# 5. O primeiro usuário a se cadastrar será o Super Admin.
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

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-dificil-de-adivinhar'
# Configuração do Banco de Dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'portal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração da API Properfy (SUBSTITUA PELO SEU TOKEN)
app.config['PROPERFY_API_TOKEN'] = '05ad4b19-08e7-4534-a594-51e3665fe0f5'
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
    <title>{% block title %}{% endblock %} - Portal Delmack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background-color: #f8f9fa; }
      .navbar { background-color: #343a40; }
      .footer { font-size: 0.9em; text-align: center; padding: 20px 0; color: #6c757d; }
      .card { margin-bottom: 1.5rem; }
      .iframe-container { position: relative; overflow: hidden; width: 100%; padding-top: 56.25%; }
      .responsive-iframe { position: absolute; top: 0; left: 0; bottom: 0; right: 0; width: 100%; height: 100%; }
    </style>
    {% block extra_css %}{% endblock %}
  </head>
  <body>
    <nav class="navbar navbar-expand-lg navbar-dark">
      <div class="container">
        <a class="navbar-brand" href="{{ url_for('index') }}">Portal Delmack</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            {% if current_user.is_authenticated %}
              {% if current_user.is_super_admin %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_dashboard') }}">Admin Dashboard</a></li>
              {% else %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}">Meu Dashboard</a></li>
              {% endif %}
              <li class="nav-item"><a class="nav-link" href="{{ url_for('imoveis') }}">IMÓVEIS</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('contratos') }}">CONTRATOS</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('graficos') }}">GRÁFICOS</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('leads') }}">LEADS</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('manutencao') }}">MANUTENÇÃO</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">Sair</a></li>
            {% else %}
              <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}">Login</a></li>
              <li class="nav-item"><a class="nav-link" href="{{ url_for('register') }}">Cadastrar</a></li>
            {% endif %}
          </ul>
        </div>
      </div>
    </nav>

    <main class="container mt-4">
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

    <footer class="footer mt-auto py-3">
      <div class="container">
        <span>Desenvolvido por: <strong>Delmack Consultoria</strong> | Contato para Suporte e Melhorias: <a href="mailto:delmackconsultoria@gmail.com">delmackconsultoria@gmail.com</a></span>
      </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
  </body>
</html>
    """,
    "index.html": """
{% extends "layout.html" %}
{% block title %}Bem-vindo{% endblock %}
{% block content %}
<div class="p-5 mb-4 bg-light rounded-3">
  <div class="container-fluid py-5">
    <h1 class="display-5 fw-bold">Bem-vindo ao Portal de Dashboards</h1>
    <p class="col-md-8 fs-4">Acesse seus relatórios de Business Intelligence de forma centralizada e segura. Faça login para continuar.</p>
    <a href="{{ url_for('login') }}" class="btn btn-primary btn-lg">Fazer Login</a>
    <a href="{{ url_for('register') }}" class="btn btn-secondary btn-lg">Cadastrar</a>
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
    <div class="card">
      <div class="card-body">
        <h3 class="card-title text-center">Login</h3>
        <form method="POST" action="{{ url_for('login') }}">
          <div class="mb-3">
            <label for="email" class="form-label">E-mail</label>
            <input type="email" class="form-control" id="email" name="email" required>
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">Senha</label>
            <input type="password" class="form-control" id="password" name="password" required>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary">Entrar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
    """,
    "register.html": """
{% extends "layout.html" %}
{% block title %}Cadastro{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-body">
        <h3 class="card-title text-center">Criar Conta</h3>
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
          <div class="d-grid">
            <button type="submit" class="btn btn-primary">Cadastrar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
    """,
    "dashboard.html": """
{% extends "layout.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
  <h2 class="mb-4">Seu Dashboard</h2>
  <div class="card">
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
{% block title %}Acesso Negado{% endblock %}
{% block content %}
<div class="alert alert-warning">
  <h4 class="alert-heading">Acesso Pendente</h4>
  <p>Você ainda não foi associado a um perfil de visualização. Por favor, entre em contato com o administrador do sistema para que ele configure seu acesso.</p>
</div>
{% endblock %}
    """,
    "imoveis.html": """
{% extends "layout.html" %}
{% block title %}Mapa de Imóveis{% endblock %}
{% block extra_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
<style>
  #map { height: 600px; width: 100%; border-radius: 0.25rem; }
  .map-container { position: relative; }
  .map-info {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1000;
    background: white;
    padding: 10px;
    border-radius: 4px;
    box-shadow: 0 0 10px rgba(0,0,0,0.2);
  }
  .valor-transacao {
    font-size: 1.3em;
    font-weight: bold;
    margin: 10px 0;
    text-align: center;
    padding: 5px;
    background-color: #f8f9fa;
    border-radius: 4px;
  }
  .valor-venda { color: #007bff; }
  .valor-aluguel { color: #28a745; }
  .popup-content {
    max-width: 280px;
  }
  .popup-line {
    margin: 5px 0;
    padding-bottom: 5px;
    border-bottom: 1px solid #eee;
  }
  .popup-header {
    font-weight: bold;
    color: #343a40;
    margin-bottom: 8px;
  }
  .popup-label {
    font-weight: 500;
    color: #495057;
  }
  .graficos-mapa {
    margin-top: 30px;
  }
  .chart-container-mapa {
    height: 350px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Mapa de Imóveis em Curitiba</h2>
  
  <div class="card">
    <div class="card-body map-container">
      <div class="map-info">
        <strong>Imóveis carregados:</strong> <span id="total-imoveis">0</span>
      </div>
      <div id="map"></div>
    </div>
  </div>

  <div class="graficos-mapa">
    <h3 class="mb-4">Análise Rápida do Portfólio</h3>
    <div class="row">
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Tipo de Transação</h5>
            <div class="chart-container-mapa">
              <canvas id="chart-transacao"></canvas>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Tipo de Imóvel</h5>
            <div class="chart-container-mapa">
              <canvas id="chart-tipo"></canvas>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Propósito do Imóvel</h5>
            <div class="chart-container-mapa">
              <canvas id="chart-proposito"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Coordenadas do centro de Curitiba
  const map = L.map('map').setView([-25.4296, -49.2719], 12);

  // Adiciona o mapa base
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // Cluster de marcadores
  let markers = L.markerClusterGroup();
  map.addLayer(markers);

  // Elementos DOM
  const totalImoveisSpan = document.getElementById('total-imoveis');

  // Formata valor monetário
  function formatarValor(valor) {
    if (!valor || valor <= 0) return 'Valor não informado';
    return 'R$ ' + parseFloat(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // Carrega dados de imóveis
  function carregarImoveis() {
    fetch('/api/imoveis')
      .then(response => {
        if (!response.ok) {
          throw new Error('Erro ao carregar dados');
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        exibirImoveis(data);
      })
      .catch(error => {
        console.error('Erro:', error);
        alert(error.message || 'Erro ao carregar imóveis');
      });
  }

  // Exibe imóveis no mapa
  function exibirImoveis(data) {
    markers.clearLayers();
    totalImoveisSpan.textContent = data.length;
    
    data.forEach(imovel => {
      if (imovel.dcmAddressLatitude && imovel.dcmAddressLongitude) {
        const marker = L.marker([imovel.dcmAddressLatitude, imovel.dcmAddressLongitude]);
        
        let valorHtml = '';
        if (imovel.chrTransactionType === 'SALE') {
          valorHtml = `<div class="valor-transacao valor-venda">${formatarValor(imovel.dcmSale)}</div>`;
        } else if (imovel.chrTransactionType === 'RENT') {
          const valorTotalAluguel = (imovel.dcmExpectedRent || 0) + (imovel.dcmCondoValue || 0);
          valorHtml = `<div class="valor-transacao valor-aluguel">${formatarValor(valorTotalAluguel)}</div>`;
        }

        const popupContent = `
          <div class="popup-content">
            <div class="popup-header">${imovel.chrCondoName}</div>
            
            <div class="popup-line">
              <span class="popup-label">Tipo:</span> ${imovel.chrType || 'Não informado'}
            </div>
            
            <div class="popup-line">
              <span class="popup-label">Endereço:</span> ${imovel.chrAddressStreet || 'Não informado'}
            </div>
            
            <div class="popup-line">
              <span class="popup-label">Bairro:</span> ${imovel.chrAddressDistrict || 'Não informado'}
            </div>
            
            <div class="popup-line">
              <span class="popup-label">CEP:</span> ${imovel.chrAddressPostalCode || 'Não informado'}
            </div>
            
            ${valorHtml}
            
            <div class="popup-line">
              <small>Lat: ${imovel.dcmAddressLatitude.toFixed(6)}, Lng: ${imovel.dcmAddressLongitude.toFixed(6)}</small>
            </div>
          </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.addLayer(marker);
      }
    });
  }

  // Carrega dados para gráficos do mapa
  function carregarGraficosMapa() {
    fetch('/api/imoveis/graficos')
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        criarGraficosMapa(data);
      })
      .catch(error => {
        console.error('Erro ao carregar dados para gráficos do mapa:', error);
      });
  }

  // Cria gráficos abaixo do mapa
  function criarGraficosMapa(data) {
    const colors = ['#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF'];

    // Gráfico de Transação
    new Chart(document.getElementById('chart-transacao'), {
      type: 'pie',
      data: {
        labels: data.transacao.labels,
        datasets: [{
          data: data.transacao.values,
          backgroundColor: colors.slice(0, 2)
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    // Gráfico de Tipo
    new Chart(document.getElementById('chart-tipo'), {
      type: 'bar',
      data: {
        labels: data.tipo.labels,
        datasets: [{
          label: 'Quantidade',
          data: data.tipo.values,
          backgroundColor: '#4BC0C0'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
    });

    // Gráfico de Propósito
    new Chart(document.getElementById('chart-proposito'), {
      type: 'doughnut',
      data: {
        labels: data.proposito.labels,
        datasets: [{
          data: data.proposito.values,
          backgroundColor: colors.slice(2, 5)
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // Carrega dados iniciais
  carregarImoveis();
  carregarGraficosMapa();
});
</script>
{% endblock %}
    """,
    "contratos.html": """
{% extends "layout.html" %}
{% block title %}Contratos de Aluguel{% endblock %}
{% block extra_css %}
<style>
  .table-container {
    max-height: 600px;
    overflow-y: auto;
  }
  .table th {
    position: sticky;
    top: 0;
    background-color: #343a40;
    color: white;
    z-index: 10;
  }
  .loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
  }
  .status-badge {
    font-size: 0.8em;
    padding: 4px 8px;
    border-radius: 12px;
  }
  .status-ativo { background-color: #d4edda; color: #155724; }
  .status-inativo { background-color: #f8d7da; color: #721c24; }
  .status-pendente { background-color: #fff3cd; color: #856404; }
  .valor-destaque {
    font-weight: bold;
    color: #28a745;
  }
  .info-card {
    background-color: #e9ecef;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Contratos de Aluguel</h2>
  
  <div class="info-card">
    <div class="row">
      <div class="col-md-3">
        <strong>Total de Contratos:</strong> <span id="total-contratos" class="text-primary">0</span>
      </div>
      <div class="col-md-3">
        <strong>Contratos Ativos:</strong> <span id="contratos-ativos" class="text-success">0</span>
      </div>
      <div class="col-md-3">
        <strong>Valor Total Mensal:</strong> <span id="valor-total" class="valor-destaque">R$ 0,00</span>
      </div>
      <div class="col-md-3">
        <button id="btn-refresh" class="btn btn-outline-primary btn-sm">
          <i class="bi bi-arrow-clockwise"></i> Atualizar
        </button>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-body">
      <div id="loading" class="loading-spinner" style="display: none;">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Carregando...</span>
        </div>
      </div>
      
      <div id="error-message" class="alert alert-danger" style="display: none;"></div>
      
      <div class="table-container">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>ID</th>
              <th>Inquilino</th>
              <th>Imóvel</th>
              <th>Endereço</th>
              <th>Valor Aluguel</th>
              <th>Data Início</th>
              <th>Data Fim</th>
              <th>Status</th>
              <th>Observações</th>
            </tr>
          </thead>
          <tbody id="contratos-tbody">
            <!-- Os dados serão inseridos aqui via JavaScript -->
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const loadingElement = document.getElementById('loading');
  const errorElement = document.getElementById('error-message');
  const tbody = document.getElementById('contratos-tbody');
  const totalContratosSpan = document.getElementById('total-contratos');
  const contratosAtivosSpan = document.getElementById('contratos-ativos');
  const valorTotalSpan = document.getElementById('valor-total');
  const btnRefresh = document.getElementById('btn-refresh');

  // Formata valor monetário
  function formatarValor(valor) {
    if (!valor || valor <= 0) return 'R$ 0,00';
    return 'R$ ' + parseFloat(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // Formata data
  function formatarData(dataString) {
    if (!dataString) return 'Não informado';
    try {
      const data = new Date(dataString);
      return data.toLocaleDateString('pt-BR');
    } catch (e) {
      return dataString;
    }
  }

  // Formata status
  function formatarStatus(status) {
    if (!status) return '<span class="status-badge status-pendente">Não informado</span>';
    
    const statusLower = status.toLowerCase();
    let className = 'status-badge ';
    
    if (statusLower.includes('ativo') || statusLower.includes('vigente')) {
      className += 'status-ativo';
    } else if (statusLower.includes('inativo') || statusLower.includes('encerrado')) {
      className += 'status-inativo';
    } else {
      className += 'status-pendente';
    }
    
    return `<span class="${className}">${status}</span>`;
  }

  // Carrega dados de contratos
  function carregarContratos() {
    loadingElement.style.display = 'flex';
    errorElement.style.display = 'none';
    tbody.innerHTML = '';

    fetch('/api/contratos')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        exibirContratos(data);
        atualizarEstatisticas(data);
      })
      .catch(error => {
        console.error('Erro:', error);
        errorElement.textContent = error.message || 'Erro ao carregar contratos';
        errorElement.style.display = 'block';
      })
      .finally(() => {
        loadingElement.style.display = 'none';
      });
  }

  // Exibe contratos na tabela
  function exibirContratos(contratos) {
    tbody.innerHTML = '';
    
    if (contratos.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Nenhum contrato encontrado</td></tr>';
      return;
    }

    contratos.forEach(contrato => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${contrato.id || 'N/A'}</td>
        <td>${contrato.tenant_name || 'Não informado'}</td>
        <td>${contrato.property_name || 'Não informado'}</td>
        <td>${contrato.property_address || 'Não informado'}</td>
        <td class="valor-destaque">${formatarValor(contrato.rent_value)}</td>
        <td>${formatarData(contrato.start_date)}</td>
        <td>${formatarData(contrato.end_date)}</td>
        <td>${formatarStatus(contrato.status)}</td>
        <td>${contrato.observations || '-'}</td>
      `;
      tbody.appendChild(row);
    });
  }

  // Atualiza estatísticas
  function atualizarEstatisticas(contratos) {
    const total = contratos.length;
    const ativos = contratos.filter(c => {
      const status = (c.status || '').toLowerCase();
      return status.includes('ativo') || status.includes('vigente');
    }).length;
    
    const valorTotal = contratos.reduce((sum, c) => {
      const valor = parseFloat(c.rent_value) || 0;
      return sum + valor;
    }, 0);

    totalContratosSpan.textContent = total;
    contratosAtivosSpan.textContent = ativos;
    valorTotalSpan.textContent = formatarValor(valorTotal);
  }

  // Event listeners
  btnRefresh.addEventListener('click', carregarContratos);

  // Carrega dados iniciais
  carregarContratos();
});
</script>
{% endblock %}
    """,
    "graficos.html": """
{% extends "layout.html" %}
{% block title %}Análise de Dados - Imóveis{% endblock %}
{% block extra_css %}
<style>
  .chart-container {
    position: relative;
    height: 400px;
    margin-bottom: 30px;
  }
  .chart-card {
    margin-bottom: 30px;
  }
  .stats-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
  }
  .stat-item {
    text-align: center;
    padding: 15px;
  }
  .stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 5px;
  }
  .stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  }
  .loading-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
  }
  .chart-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 15px;
    color: #495057;
  }
  .filter-section {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 30px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Análise de Dados - Imóveis</h2>
  
  <!-- Loading Overlay -->
  <div id="loading-overlay" class="loading-overlay" style="display: none;">
    <div class="loading-content">
      <div class="spinner-border text-primary mb-3" role="status"></div>
      <h5>Carregando dados...</h5>
      <p class="text-muted">Processando informações dos imóveis</p>
    </div>
  </div>

  <!-- Estatísticas Gerais -->
  <div class="stats-card">
    <div class="row">
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="total-imoveis">0</div>
          <div class="stat-label">Total de Imóveis</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="valor-medio">R$ 0</div>
          <div class="stat-label">Valor Médio de Venda</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="area-media">0m²</div>
          <div class="stat-label">Área Média</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="ano-medio">0</div>
          <div class="stat-label">Ano Médio de Construção</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Filtros -->
  <div class="filter-section">
    <div class="row">
      <div class="col-md-4">
        <button id="btn-refresh" class="btn btn-primary">
          <i class="bi bi-arrow-clockwise"></i> Atualizar Dados
        </button>
      </div>
      <div class="col-md-8">
        <div class="text-end">
          <small class="text-muted">Última atualização: <span id="last-update">-</span></small>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráficos -->
  <div class="row">
    <!-- Gráfico de Tipos de Imóveis -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Distribuição por Tipo de Imóvel</div>
          <div class="chart-container">
            <canvas id="chart-tipos"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Condições -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Condição dos Imóveis</div>
          <div class="chart-container">
            <canvas id="chart-condicoes"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Garagens -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Distribuição de Vagas de Garagem</div>
          <div class="chart-container">
            <canvas id="chart-garagens"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Anos de Construção -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Imóveis por Década de Construção</div>
          <div class="chart-container">
            <canvas id="chart-decadas"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Valores de Venda -->
    <div class="col-md-12">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Distribuição de Valores de Venda</div>
          <div class="chart-container">
            <canvas id="chart-valores"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Área vs Valor -->
    <div class="col-md-12">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Relação entre Área Privativa e Valor de Venda</div>
          <div class="chart-container">
            <canvas id="chart-area-valor"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Mensagem de Erro -->
  <div id="error-message" class="alert alert-danger" style="display: none;"></div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const loadingOverlay = document.getElementById('loading-overlay');
  const errorElement = document.getElementById('error-message');
  const btnRefresh = document.getElementById('btn-refresh');
  
  // Elementos de estatísticas
  const totalImoveisSpan = document.getElementById('total-imoveis');
  const valorMedioSpan = document.getElementById('valor-medio');
  const areaMediaSpan = document.getElementById('area-media');
  const anoMedioSpan = document.getElementById('ano-medio');
  const lastUpdateSpan = document.getElementById('last-update');

  // Variáveis para armazenar os gráficos
  let charts = {};

  // Cores para os gráficos
  const colors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
  ];

  // Formata valor monetário
  function formatarValor(valor) {
    if (!valor || valor <= 0) return 'R$ 0';
    return 'R$ ' + parseFloat(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }

  // Formata área
  function formatarArea(area) {
    if (!area || area <= 0) return '0m²';
    return parseFloat(area).toLocaleString('pt-BR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }) + 'm²';
  }

  // Carrega dados para gráficos
  function carregarDadosGraficos() {
    loadingOverlay.style.display = 'flex';
    errorElement.style.display = 'none';

    fetch('/api/graficos')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        atualizarEstatisticas(data.statistics);
        criarGraficos(data.charts);
        lastUpdateSpan.textContent = new Date().toLocaleString('pt-BR');
      })
      .catch(error => {
        console.error('Erro:', error);
        errorElement.textContent = error.message || 'Erro ao carregar dados para gráficos';
        errorElement.style.display = 'block';
      })
      .finally(() => {
        loadingOverlay.style.display = 'none';
      });
  }

  // Atualiza estatísticas gerais
  function atualizarEstatisticas(stats) {
    totalImoveisSpan.textContent = stats.total_imoveis || 0;
    valorMedioSpan.textContent = formatarValor(stats.valor_medio);
    areaMediaSpan.textContent = formatarArea(stats.area_media);
    anoMedioSpan.textContent = Math.round(stats.ano_medio) || 0;
  }

  // Destroi gráficos existentes
  function destruirGraficos() {
    Object.values(charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    charts = {};
  }

  // Cria todos os gráficos
  function criarGraficos(data) {
    destruirGraficos();

    // Gráfico de Tipos de Imóveis
    if (data.tipos && data.tipos.labels.length > 0) {
      charts.tipos = new Chart(document.getElementById('chart-tipos'), {
        type: 'pie',
        data: {
          labels: data.tipos.labels,
          datasets: [{
            data: data.tipos.values,
            backgroundColor: colors.slice(0, data.tipos.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Condições
    if (data.condicoes && data.condicoes.labels.length > 0) {
      charts.condicoes = new Chart(document.getElementById('chart-condicoes'), {
        type: 'doughnut',
        data: {
          labels: data.condicoes.labels,
          datasets: [{
            data: data.condicoes.values,
            backgroundColor: colors.slice(0, data.condicoes.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Garagens
    if (data.garagens && data.garagens.labels.length > 0) {
      charts.garagens = new Chart(document.getElementById('chart-garagens'), {
        type: 'bar',
        data: {
          labels: data.garagens.labels,
          datasets: [{
            label: 'Quantidade de Imóveis',
            data: data.garagens.values,
            backgroundColor: '#36A2EB'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Gráfico de Décadas
    if (data.decadas && data.decadas.labels.length > 0) {
      charts.decadas = new Chart(document.getElementById('chart-decadas'), {
        type: 'line',
        data: {
          labels: data.decadas.labels,
          datasets: [{
            label: 'Imóveis Construídos',
            data: data.decadas.values,
            borderColor: '#FF6384',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Gráfico de Valores
    if (data.valores && data.valores.labels.length > 0) {
      charts.valores = new Chart(document.getElementById('chart-valores'), {
        type: 'bar',
        data: {
          labels: data.valores.labels,
          datasets: [{
            label: 'Quantidade de Imóveis',
            data: data.valores.values,
            backgroundColor: '#FFCE56'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Gráfico de Área vs Valor
    if (data.area_valor && data.area_valor.length > 0) {
      charts.areaValor = new Chart(document.getElementById('chart-area-valor'), {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Área vs Valor',
            data: data.area_valor,
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: '#4BC0C0'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Área Privativa (m²)'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Valor de Venda (R$)'
              }
            }
          }
        }
      });
    }
  }

  // Event listeners
  btnRefresh.addEventListener('click', carregarDadosGraficos);

  // Carrega dados iniciais
  carregarDadosGraficos();
});
</script>
{% endblock %}
    """,
    "leads.html": """
{% extends "layout.html" %}
{% block title %}Análise de Leads - CRM{% endblock %}
{% block extra_css %}
<style>
  .chart-container {
    position: relative;
    height: 400px;
    margin-bottom: 30px;
  }
  .chart-card {
    margin-bottom: 30px;
  }
  .stats-card {
    background: linear-gradient(135deg, #2980b9 0%, #2c3e50 100%);
    color: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
  }
  .stat-item {
    text-align: center;
    padding: 15px;
  }
  .stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 5px;
  }
  .stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  }
  .loading-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
  }
  .chart-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 15px;
    color: #495057;
  }
  .filter-section {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 30px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Análise de Leads - CRM</h2>
  
  <!-- Loading Overlay -->
  <div id="loading-overlay" class="loading-overlay" style="display: none;">
    <div class="loading-content">
      <div class="spinner-border text-primary mb-3" role="status"></div>
      <h5>Carregando dados...</h5>
      <p class="text-muted">Processando informações de Leads</p>
    </div>
  </div>

  <!-- Estatísticas Gerais -->
  <div class="stats-card">
    <div class="row">
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="total-leads">0</div>
          <div class="stat-label">Total de Leads</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="total-cards">0</div>
          <div class="stat-label">Total de Cards</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="cards-concluidos">0</div>
          <div class="stat-label">Cards Concluídos</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="taxa-conversao">0%</div>
          <div class="stat-label">Taxa de Conversão</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Filtros -->
  <div class="filter-section">
    <div class="row">
      <div class="col-md-4">
        <button id="btn-refresh" class="btn btn-primary">
          <i class="bi bi-arrow-clockwise"></i> Atualizar Dados
        </button>
      </div>
      <div class="col-md-8">
        <div class="text-end">
          <small class="text-muted">Última atualização: <span id="last-update">-</span></small>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráficos -->
  <div class="row">
    <!-- Gráfico de Canais de Aquisição -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Canais de Aquisição de Leads</div>
          <div class="chart-container">
            <canvas id="chart-canais"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Status dos Cards -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Status dos Cards</div>
          <div class="chart-container">
            <canvas id="chart-status-cards"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Tipos de Transação -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Tipos de Transação</div>
          <div class="chart-container">
            <canvas id="chart-transacoes"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Estágios do Pipeline -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Leads por Estágio do Pipeline</div>
          <div class="chart-container">
            <canvas id="chart-pipeline"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Mensagem de Erro -->
  <div id="error-message" class="alert alert-danger" style="display: none;"></div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const loadingOverlay = document.getElementById('loading-overlay');
  const errorElement = document.getElementById('error-message');
  const btnRefresh = document.getElementById('btn-refresh');
  
  // Elementos de estatísticas
  const totalLeadsSpan = document.getElementById('total-leads');
  const totalCardsSpan = document.getElementById('total-cards');
  const cardsConcluidosSpan = document.getElementById('cards-concluidos');
  const taxaConversaoSpan = document.getElementById('taxa-conversao');
  const lastUpdateSpan = document.getElementById('last-update');

  // Variáveis para armazenar os gráficos
  let charts = {};

  // Cores para os gráficos
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6',
    '#1abc9c', '#d35400', '#34495e', '#7f8c8d', '#bdc3c7'
  ];

  // Carrega dados para gráficos de leads
  function carregarDadosLeads() {
    loadingOverlay.style.display = 'flex';
    errorElement.style.display = 'none';

    fetch('/api/leads')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        atualizarEstatisticas(data.statistics);
        criarGraficos(data.charts);
        lastUpdateSpan.textContent = new Date().toLocaleString('pt-BR');
      })
      .catch(error => {
        console.error('Erro:', error);
        errorElement.textContent = error.message || 'Erro ao carregar dados de Leads';
        errorElement.style.display = 'block';
      })
      .finally(() => {
        loadingOverlay.style.display = 'none';
      });
  }

  // Atualiza estatísticas gerais
  function atualizarEstatisticas(stats) {
    totalLeadsSpan.textContent = stats.total_leads || 0;
    totalCardsSpan.textContent = stats.total_cards || 0;
    cardsConcluidosSpan.textContent = stats.cards_concluidos || 0;
    taxaConversaoSpan.textContent = (stats.taxa_conversao || 0).toFixed(1) + '%';
  }

  // Destroi gráficos existentes
  function destruirGraficos() {
    Object.values(charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    charts = {};
  }

  // Cria todos os gráficos
  function criarGraficos(data) {
    destruirGraficos();

    // Gráfico de Canais de Aquisição
    if (data.canais && data.canais.labels.length > 0) {
      charts.canais = new Chart(document.getElementById('chart-canais'), {
        type: 'pie',
        data: {
          labels: data.canais.labels,
          datasets: [{
            data: data.canais.values,
            backgroundColor: colors.slice(0, data.canais.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Status dos Cards
    if (data.status_cards && data.status_cards.labels.length > 0) {
      charts.statusCards = new Chart(document.getElementById('chart-status-cards'), {
        type: 'doughnut',
        data: {
          labels: data.status_cards.labels,
          datasets: [{
            data: data.status_cards.values,
            backgroundColor: colors.slice(0, data.status_cards.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Tipos de Transação
    if (data.transacoes && data.transacoes.labels.length > 0) {
      charts.transacoes = new Chart(document.getElementById('chart-transacoes'), {
        type: 'bar',
        data: {
          labels: data.transacoes.labels,
          datasets: [{
            label: 'Quantidade de Leads',
            data: data.transacoes.values,
            backgroundColor: '#2ecc71'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Gráfico de Pipeline
    if (data.pipeline && data.pipeline.labels.length > 0) {
      charts.pipeline = new Chart(document.getElementById('chart-pipeline'), {
        type: 'bar',
        data: {
          labels: data.pipeline.labels,
          datasets: [{
            label: 'Leads no Estágio',
            data: data.pipeline.values,
            backgroundColor: '#9b59b6'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y', // Funil horizontal
          scales: {
            x: {
              beginAtZero: true
            }
          }
        }
      });
    }
  }

  // Event listeners
  btnRefresh.addEventListener('click', carregarDadosLeads);

  // Carrega dados iniciais
  carregarDadosLeads();
});
</script>
{% endblock %}
    """,
    "manutencao.html": """
{% extends "layout.html" %}
{% block title %}Análise de Manutenção{% endblock %}
{% block extra_css %}
<style>
  .chart-container {
    position: relative;
    height: 400px;
    margin-bottom: 30px;
  }
  .chart-card {
    margin-bottom: 30px;
  }
  .stats-card {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    color: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
  }
  .stat-item {
    text-align: center;
    padding: 15px;
  }
  .stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 5px;
  }
  .stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  }
  .loading-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
  }
  .chart-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 15px;
    color: #495057;
  }
  .filter-section {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 30px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Análise de Manutenção</h2>
  
  <!-- Loading Overlay -->
  <div id="loading-overlay" class="loading-overlay" style="display: none;">
    <div class="loading-content">
      <div class="spinner-border text-primary mb-3" role="status"></div>
      <h5>Carregando dados...</h5>
      <p class="text-muted">Processando informações de Manutenção</p>
    </div>
  </div>

  <!-- Estatísticas Gerais -->
  <div class="stats-card">
    <div class="row">
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="total-manutencoes">0</div>
          <div class="stat-label">Total de Manutenções</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="alta-prioridade">0</div>
          <div class="stat-label">Alta Prioridade</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="pendentes">0</div>
          <div class="stat-label">Pendentes</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-item">
          <div class="stat-number" id="concluidas">0</div>
          <div class="stat-label">Concluídas</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Filtros -->
  <div class="filter-section">
    <div class="row">
      <div class="col-md-4">
        <button id="btn-refresh" class="btn btn-primary">
          <i class="bi bi-arrow-clockwise"></i> Atualizar Dados
        </button>
      </div>
      <div class="col-md-8">
        <div class="text-end">
          <small class="text-muted">Última atualização: <span id="last-update">-</span></small>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráficos -->
  <div class="row">
    <!-- Gráfico de Prioridades -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Distribuição por Prioridade</div>
          <div class="chart-container">
            <canvas id="chart-prioridades"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Status -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Status das Manutenções</div>
          <div class="chart-container">
            <canvas id="chart-status"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Responsáveis -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Manutenções por Responsável</div>
          <div class="chart-container">
            <canvas id="chart-responsaveis"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfico de Categorias -->
    <div class="col-md-6">
      <div class="card chart-card">
        <div class="card-body">
          <div class="chart-title">Categorias de Manutenção</div>
          <div class="chart-container">
            <canvas id="chart-categorias"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Mensagem de Erro -->
  <div id="error-message" class="alert alert-danger" style="display: none;"></div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const loadingOverlay = document.getElementById('loading-overlay');
  const errorElement = document.getElementById('error-message');
  const btnRefresh = document.getElementById('btn-refresh');
  
  // Elementos de estatísticas
  const totalManutencoesSpan = document.getElementById('total-manutencoes');
  const altaPrioridadeSpan = document.getElementById('alta-prioridade');
  const pendentesSpan = document.getElementById('pendentes');
  const concluidasSpan = document.getElementById('concluidas');
  const lastUpdateSpan = document.getElementById('last-update');

  // Variáveis para armazenar os gráficos
  let charts = {};

  // Cores para os gráficos
  const colors = [
    '#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db',
    '#9b59b6', '#1abc9c', '#34495e', '#95a5a6', '#e67e22'
  ];

  // Carrega dados para gráficos de manutenção
  function carregarDadosManutencao() {
    loadingOverlay.style.display = 'flex';
    errorElement.style.display = 'none';

    fetch('/api/manutencao_graficos')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        atualizarEstatisticas(data.statistics);
        criarGraficos(data.charts);
        lastUpdateSpan.textContent = new Date().toLocaleString('pt-BR');
      })
      .catch(error => {
        console.error('Erro:', error);
        errorElement.textContent = error.message || 'Erro ao carregar dados de Manutenção';
        errorElement.style.display = 'block';
      })
      .finally(() => {
        loadingOverlay.style.display = 'none';
      });
  }

  // Atualiza estatísticas gerais
  function atualizarEstatisticas(stats) {
    totalManutencoesSpan.textContent = stats.total_manutencoes || 0;
    altaPrioridadeSpan.textContent = stats.alta_prioridade || 0;
    pendentesSpan.textContent = stats.pendentes || 0;
    concluidasSpan.textContent = stats.concluidas || 0;
  }

  // Destroi gráficos existentes
  function destruirGraficos() {
    Object.values(charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    charts = {};
  }

  // Cria todos os gráficos
  function criarGraficos(data) {
    destruirGraficos();

    // Gráfico de Prioridades
    if (data.prioridades && data.prioridades.labels.length > 0) {
      charts.prioridades = new Chart(document.getElementById('chart-prioridades'), {
        type: 'pie',
        data: {
          labels: data.prioridades.labels,
          datasets: [{
            data: data.prioridades.values,
            backgroundColor: ['#e74c3c', '#f39c12', '#2ecc71'].slice(0, data.prioridades.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Status
    if (data.status && data.status.labels.length > 0) {
      charts.status = new Chart(document.getElementById('chart-status'), {
        type: 'doughnut',
        data: {
          labels: data.status.labels,
          datasets: [{
            data: data.status.values,
            backgroundColor: colors.slice(0, data.status.labels.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // Gráfico de Responsáveis
    if (data.responsaveis && data.responsaveis.labels.length > 0) {
      charts.responsaveis = new Chart(document.getElementById('chart-responsaveis'), {
        type: 'bar',
        data: {
          labels: data.responsaveis.labels,
          datasets: [{
            label: 'Quantidade de Manutenções',
            data: data.responsaveis.values,
            backgroundColor: '#3498db'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Gráfico de Categorias
    if (data.categorias && data.categorias.labels.length > 0) {
      charts.categorias = new Chart(document.getElementById('chart-categorias'), {
        type: 'bar',
        data: {
          labels: data.categorias.labels,
          datasets: [{
            label: 'Quantidade de Manutenções',
            data: data.categorias.values,
            backgroundColor: '#9b59b6'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y', // Barras horizontais
          scales: {
            x: {
              beginAtZero: true
            }
          }
        }
      });
    }
  }

  // Event listeners
  btnRefresh.addEventListener('click', carregarDadosManutencao);

  // Carrega dados iniciais
  carregarDadosManutencao();
});
</script>
{% endblock %}
    """,
    "admin/admin_layout.html": """
{% extends "layout.html" %}
{% block content %}
<div class="row">
    <div class="col-md-3">
        <div class="list-group">
            <a href="{{ url_for('admin_dashboard') }}" class="list-group-item list-group-item-action {% if request.endpoint == 'admin_dashboard' %}active{% endif %}">Visão Geral</a>
            <a href="{{ url_for('admin_users') }}" class="list-group-item list-group-item-action {% if request.endpoint == 'admin_users' %}active{% endif %}">Gerenciar Usuários</a>
            <a href="{{ url_for('admin_companies') }}" class="list-group-item list-group-item-action {% if request.endpoint == 'admin_companies' %}active{% endif %}">Gerenciar Empresas</a>
            <a href="{{ url_for('admin_profiles') }}" class="list-group-item list-group-item-action {% if request.endpoint == 'admin_profiles' %}active{% endif %}">Gerenciar Perfis</a>
        </div>
    </div>
    <div class="col-md-9">
        {% block admin_content %}{% endblock %}
    </div>
</div>
{% endblock %}
    """,
    "admin/admin_dashboard.html": """
{% extends "admin/admin_layout.html" %}
{% block title %}Admin Dashboard{% endblock %}
{% block admin_content %}
<h3>Visão Geral da Plataforma</h3>
<div class="row">
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">Usuários Totais</h5>
                <p class="card-text fs-2">{{ stats.total_users }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">Empresas Cadastradas</h5>
                <p class="card-text fs-2">{{ stats.total_companies }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">Perfis de Acesso</h5>
                <p class="card-text fs-2">{{ stats.total_profiles }}</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
    """,
    "admin/admin_users.html": """
{% extends "admin/admin_layout.html" %}
{% block title %}Gerenciar Usuários{% endblock %}
{% block admin_content %}
<h3>Gerenciar Usuários</h3>
<div class="card">
    <div class="card-body">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Email</th>
                    <th>Empresa</th>
                    <th>Perfil</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <form method="POST" action="{{ url_for('admin_update_user', user_id=user.id) }}">
                        <td>{{ user.id }}</td>
                        <td>{{ user.username }} {% if user.is_super_admin %}<span class="badge bg-primary">Admin</span>{% endif %}</td>
                        <td>{{ user.email }}</td>
                        <td>
                            <select name="company_id" class="form-select">
                                <option value="">Nenhuma</option>
                                {% for company in companies %}
                                <option value="{{ company.id }}" {% if user.company_id == company.id %}selected{% endif %}>{{ company.name }}</option>
                                {% endfor %}
                            </select>
                        </td>
                        <td>
                            <select name="profile_id" class="form-select">
                                <option value="">Nenhum</option>
                                {% for profile in profiles %}
                                <option value="{{ profile.id }}" {% if user.profile_id == profile.id %}selected{% endif %}>{{ profile.name }}</option>
                                {% endfor %}
                            </select>
                        </td>
                        <td>
                            <button type="submit" class="btn btn-success btn-sm">Salvar</button>
                    </form>
                    <form method="POST" action="{{ url_for('admin_delete_user', user_id=user.id) }}" onsubmit="return confirm('Tem certeza que deseja deletar este usuário?');" style="display:inline;">
                        <button type="submit" class="btn btn-danger btn-sm" {% if user.is_super_admin %}disabled{% endif %}>Deletar</button>
                    </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
    """,
    "admin/admin_companies.html": """
{% extends "admin/admin_layout.html" %}
{% block title %}Gerenciar Empresas{% endblock %}
{% block admin_content %}
<h3>Gerenciar Empresas</h3>
<div class="card mb-4">
    <div class="card-body">
        <h5 class="card-title">Adicionar Nova Empresa</h5>
        <form method="POST">
            <div class="input-group">
                <input type="text" name="name" class="form-control" placeholder="Nome da nova empresa" required>
                <button class="btn btn-primary" type="submit">Adicionar</button>
            </div>
        </form>
    </div>
</div>
<div class="card">
    <div class="card-body">
        <h5 class="card-title">Empresas Cadastradas</h5>
        <ul class="list-group">
            {% for company in companies %}
            <li class="list-group-item">{{ company.name }}</li>
            {% endfor %}
        </ul>
    </div>
</div>
{% endblock %}
    """,
    "admin/admin_profiles.html": """
{% extends "admin/admin_layout.html" %}
{% block title %}Gerenciar Perfis{% endblock %}
{% block admin_content %}
<h3>Gerenciar Perfis de Acesso</h3>
<div class="card mb-4">
    <div class="card-body">
        <h5 class="card-title">Adicionar Novo Perfil</h5>
        <form method="POST">
            <div class="mb-3">
                <label for="name" class="form-label">Nome do Perfil</label>
                <input type="text" name="name" id="name" class="form-control" placeholder="Ex: Diretor Financeiro" required>
            </div>
            <div class="mb-3">
                <label for="report_url" class="form-label">URL Pública do Relatório Power BI</label>
                <input type="url" name="report_url" id="report_url" class="form-control" placeholder="Cole a URL pública aqui" required>
            </div>
            <button class="btn btn-primary" type="submit">Adicionar Perfil</button>
        </form>
    </div>
</div>
<div class="card">
    <div class="card-body">
        <h5 class="card-title">Perfis Cadastrados</h5>
        <table class="table">
            <thead>
                <tr><th>Nome do Perfil</th><th>URL do Relatório</th></tr>
            </thead>
            <tbody>
                {% for profile in profiles %}
                <tr><td>{{ profile.name }}</td><td><a href="{{ profile.report_url }}" target="_blank">Link</a></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
    """
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

# --- NOVA ROTA PARA CONTRATOS ---
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

# --- NOVA ROTA PARA GRÁFICOS ---
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

# --- NOVA ROTA PARA LEADS ---
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

# --- NOVA ROTA PARA MANUTENÇÃO ---
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


