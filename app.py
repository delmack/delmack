import json
import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from collections import Counter, defaultdict
from functools import wraps
import random

# --- Configuração da Aplicação Flask ---
app = Flask(__name__)
app.secret_key = 'baggio_portal_secret_key_12345'

# --- Funções Auxiliares de Gestão de Dados ---
def carregar_dados(ficheiro):
    try:
        with open(ficheiro, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if 'users.json' in ficheiro else []

def guardar_dados(dados, ficheiro):
    with open(ficheiro, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- Decorador para Controle de Acesso ---
def login_obrigatorio(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'username' not in session:
                flash('Acesso negado. Por favor, faça o login.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Você não tem permissão para aceder a esta funcionalidade.', 'danger')
                return redirect(url_for('admin_portal'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- Rotas de Autenticação ---
@app.route('/')
def home(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        users = carregar_dados('users.json')
        user_data = users.get(username, {})
        if user_data.get('password') == password:
            session['username'], session['role'] = username, user_data['role']
            return redirect(url_for('admin_portal'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada com segurança.', 'info')
    return redirect(url_for('login'))

# --- Endpoints de API Interna (Backend para Frontend) ---
@app.route('/api/proxy/map-data')
@login_obrigatorio()
def proxy_map_data():
    # ... (código da função proxy_map_data)
    return jsonify([]) # Simulação para evitar erros de API externa

@app.route('/api/proxy/map-stats')
@login_obrigatorio()
def proxy_map_stats():
    # ... (código da função proxy_map_stats)
    return jsonify({}) # Simulação

@app.route('/api/proxy/maintenance')
@login_obrigatorio()
def proxy_maintenance_data():
    # ... (código da função proxy_maintenance_data)
    return jsonify([]) # Simulação

# --- Rotas Principais da Aplicação ---
@app.route('/admin')
@login_obrigatorio()
def admin_portal(): return render_template('admin.html')

# CORREÇÃO: Rota /mapa restaurada
@app.route('/mapa')
@login_obrigatorio()
def mapa():
    return render_template('mapa.html')

# CORREÇÃO: Rota /manutencao restaurada
@app.route('/manutencao')
@login_obrigatorio()
def manutencao():
    return render_template('manutencao.html')

# --- Rotas do Módulo de Gestão de TI (Kanban) ---
@app.route('/ti')
@login_obrigatorio(role='ti_admin')
def ti_kanban():
    tasks = carregar_dados('tasks.json')
    board = {
        "Backlog": sorted([t for t in tasks if t['status'] == 'Backlog'], key=lambda x: x.get('id', 0)),
        "Analyze": sorted([t for t in tasks if t['status'] == 'Analyze'], key=lambda x: x.get('id', 0)),
        "Doing": sorted([t for t in tasks if t['status'] == 'Doing'], key=lambda x: x.get('id', 0)),
        "Concluded": sorted([t for t in tasks if t['status'] == 'Concluded'], key=lambda x: x.get('id', 0))
    }
    status_counts = {status: len(cards) for status, cards in board.items()}
    responsible_counts = Counter(t.get('responsavel', 'N/A') for t in tasks)
    priority_counts = Counter(t.get('prioridade', 'N/A') for t in tasks)
    time_by_priority = defaultdict(list)
    for task in tasks:
        if task['status'] == 'Concluded':
            time_by_priority[task.get('prioridade', 'N/A')].append(random.uniform(1, 48))
    avg_time_by_priority = {p: sum(times)/len(times) for p, times in time_by_priority.items()}
    
    return render_template(
        'ti_kanban.html',
        board=board, total_tasks=len(tasks), status_counts=status_counts,
        chart_status_labels=list(status_counts.keys()), chart_status_data=list(status_counts.values()),
        chart_responsible_labels=list(responsible_counts.keys()), chart_responsible_data=list(responsible_counts.values()),
        chart_priority_labels=list(priority_counts.keys()), chart_priority_data=list(priority_counts.values()),
        chart_time_priority_labels=list(avg_time_by_priority.keys()), chart_time_priority_data=[round(v, 2) for v in avg_time_by_priority.values()]
    )

@app.route('/ti/nova_tarefa', methods=['POST'])
@login_obrigatorio(role='ti_admin')
def nova_tarefa_ti():
    tasks = carregar_dados('tasks.json')
    nova_task = {
        "id": (tasks[-1]['id'] + 1) if tasks else 1,
        "titulo": request.form['titulo'], "descricao": request.form['descricao'],
        "responsavel": request.form['responsavel'], "prioridade": request.form['prioridade'],
        "status": request.form['status'], "criado_por": session['username'],
        "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "notas": []
    }
    tasks.append(nova_task)
    guardar_dados(tasks, 'tasks.json')
    flash('Tarefa criada com sucesso!', 'success')
    return redirect(url_for('ti_kanban'))

@app.route('/ti/mover_tarefa', methods=['POST'])
@login_obrigatorio(role='ti_admin')
def mover_tarefa():
    task_id, novo_status = int(request.form['task_id']), request.form['novo_status']
    tasks = carregar_dados('tasks.json')
    for task in tasks:
        if task.get('id') == task_id:
            task['status'] = novo_status
            break
    guardar_dados(tasks, 'tasks.json')
    return jsonify({"success": True})

# --- Rotas do Módulo de Chamados de TI ---
@app.route('/chamado_ti')
@login_obrigatorio()
def chamado_ti():
    tickets = carregar_dados('tickets.json')
    board = {
        "Aberto": sorted([t for t in tickets if t['status'] == 'Aberto'], key=lambda x: x.get('id', 0)),
        "Em Andamento": sorted([t for t in tickets if t['status'] == 'Em Andamento'], key=lambda x: x.get('id', 0)),
        "Concluído": sorted([t for t in tickets if t['status'] == 'Concluído'], key=lambda x: x.get('id', 0))
    }
    status_counts = {status: len(cards) for status, cards in board.items()}
    chamados_por_mes = Counter(datetime.datetime.strptime(t['data_criacao'], "%d/%m/%Y %H:%M").strftime("%Y-%m") for t in tickets)
    meses_ordenados = sorted(chamados_por_mes.keys())
    criadores_counts = Counter(t.get('criado_por', 'N/A') for t in tickets)
    total_resolution_time, concluded_count = 0, 0
    time_by_priority = defaultdict(list)
    for ticket in tickets:
        if ticket['status'] == 'Concluído':
            simulated_time = random.uniform(0.5, 24)
            total_resolution_time += simulated_time
            concluded_count += 1
            time_by_priority[ticket.get('prioridade', 'N/A')].append(simulated_time)
    avg_time_geral = (total_resolution_time / concluded_count) if concluded_count > 0 else 0
    avg_time_by_priority = {p: sum(times)/len(times) for p, times in time_by_priority.items()}

    return render_template(
        'chamado_ti.html',
        board=board, user_role=session.get('role'), total_tickets=len(tickets), status_counts=status_counts,
        chart_status_labels=list(status_counts.keys()), chart_status_data=list(status_counts.values()),
        chart_monthly_labels=[datetime.datetime.strptime(m, "%Y-%m").strftime("%b/%y") for m in meses_ordenados],
        chart_monthly_data=[chamados_por_mes[m] for m in meses_ordenados],
        chart_creators_labels=list(criadores_counts.keys()), chart_creators_data=list(criadores_counts.values()),
        avg_time_geral=round(avg_time_geral, 2),
        chart_time_priority_labels=list(avg_time_by_priority.keys()), chart_time_priority_data=[round(v, 2) for v in avg_time_by_priority.values()]
    )

@app.route('/chamado_ti/novo', methods=['POST'])
@login_obrigatorio()
def novo_chamado():
    tickets = carregar_dados('tickets.json')
    novo_ticket = {
        "id": (tickets[-1]['id'] + 1) if tickets else 1,
        "titulo": request.form['titulo'], "descricao": request.form['descricao'],
        "prioridade": request.form['prioridade'],
        "criado_por": session['username'], "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "Aberto", "notas": []
    }
    tickets.append(novo_ticket)
    guardar_dados(tickets, 'tickets.json')
    flash('Chamado aberto com sucesso!', 'success')
    return redirect(url_for('chamado_ti'))

@app.route('/chamado_ti/mover', methods=['POST'])
@login_obrigatorio(role='ti_admin')
def mover_chamado():
    ticket_id, novo_status = int(request.form['ticket_id']), request.form['novo_status']
    tickets = carregar_dados('tickets.json')
    for ticket in tickets:
        if ticket.get('id') == ticket_id:
            ticket['status'] = novo_status
            break
    guardar_dados(tickets, 'tickets.json')
    return jsonify({"success": True})

# --- Rota Genérica para Páginas em Desenvolvimento ---
@app.route('/menu/<pagina>')
@login_obrigatorio()
def pagina_menu(pagina):
    flash(f'A página "{pagina.capitalize()}" será implementada em breve!', 'info')
    return redirect(url_for('admin_portal'))

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    app.run(debug=True)
