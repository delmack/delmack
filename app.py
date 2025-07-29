import json
import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from collections import Counter
from functools import wraps

app = Flask(__name__)
app.secret_key = 'baggio_portal_secret_key_12345'

# --- Funções de Gestão de Dados ---
def carregar_dados(ficheiro):
    try:
        with open(ficheiro, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if ficheiro == 'tickets.json' else {}

def guardar_dados(dados, ficheiro):
    with open(ficheiro, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- Decorador de Login ---
def login_obrigatorio(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'username' not in session:
                flash('Acesso negado. Por favor, faça o login.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') not in role:
                flash('Você não tem permissão para aceder a esta funcionalidade.', 'danger')
                return redirect(url_for('admin_portal'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- Rotas de Autenticação ---
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('admin_portal'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = carregar_dados('users.json')
        user_data = users.get(username)
        if user_data and user_data['password'] == password:
            session['username'] = username
            session['role'] = user_data['role']
            return redirect(url_for('admin_portal'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada com segurança.', 'info')
    return redirect(url_for('login'))

# --- API Endpoints ---
@app.route('/api/map-data')
@login_obrigatorio()
def api_map_data():
    try:
        api_url = "https://sandbox.properfy.com.br/api/property/property"
        headers = {"Authorization": "Bearer ac216f84-8e3f-4349-9ffa-884748149b89"}
        params = {"page": 1, "size": 5000}
        
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        properties = response.json().get('content', [])
        filtered_properties = []
        
        for prop in properties:
            lat = prop.get('dcmAddressLatitude')
            lng = prop.get('dcmAddressLongitude')
            
            if lat and lng:
                try:
                    lat = float(lat)
                    lng = float(lng)
                    if (-33.75 <= lat <= -22.52) and (-57.65 <= lng <= -48.02):
                        filtered_properties.append(prop)
                except (ValueError, TypeError):
                    continue
        
        return jsonify(filtered_properties)
    
    except requests.exceptions.Timeout:
        app.logger.error("API Timeout")
        return jsonify({"error": "A API demorou muito para responder"}), 504
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API Request Error: {str(e)}")
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 502
    except Exception as e:
        app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500

@app.route('/api/map-stats')
@login_obrigatorio()
def api_map_stats():
    try:
        api_url = "https://sandbox.properfy.com.br/api/property/property"
        headers = {"Authorization": "Bearer ac216f84-8e3f-4349-9ffa-884748149b89"}
        params = {"page": 1, "size": 5000}
        
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        properties = response.json().get('content', [])
        api_stats = {
            "total_properties": len(properties),
            "by_type": Counter(prop.get('chrType', 'N/A') for prop in properties),
            "by_transaction": Counter(prop.get('chrTransactionType', 'N/A') for prop in properties),
            "error": None
        }
        
        return jsonify(api_stats)
    
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout ao acessar a API"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500

# --- Rotas Principais ---
@app.route('/admin')
@login_obrigatorio()
def admin_portal():
    return render_template('admin.html')

@app.route('/mapa')
@login_obrigatorio()
def mapa():
    return render_template('mapa.html', default_coords=[-25.4284, -49.2733])

@app.route('/imoveis')
@login_obrigatorio()
def imoveis():
    try:
        api_url = "https://sandbox.properfy.com.br/api/property/property"
        headers = {"Authorization": "Bearer ac216f84-8e3f-4349-9ffa-884748149b89"}
        params = {"page": 1, "size": 5000}
        
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        properties = response.json().get('content', [])
        stats = {
            "total": len(properties),
            "by_name": Counter(prop.get('chrName', 'N/A') for prop in properties),
            "by_active": Counter('Ativo' if prop.get('isActive') else 'Inativo' for prop in properties),
            "by_state": Counter(prop.get('address', {}).get('state', 'N/A') for prop in properties),
            "error": None
        }
        
    except Exception as e:
        stats = {"error": str(e)}
    
    return render_template('imoveis.html', stats=stats)

@app.route('/crm')
@login_obrigatorio()
def crm():
    try:
        api_url = "https://sandbox.properfy.com.br/api/crm/lead"
        headers = {"Authorization": "Bearer ac216f84-8e3f-4349-9ffa-884748149b89"}
        params = {"filter": "", "size": 500}
        
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        leads = response.json().get('content', [])
        stats = {
            "total": len(leads),
            "by_name": Counter(lead.get('chrName', 'N/A') for lead in leads),
            "by_channel": Counter(lead.get('chrAcquisitionChannel', 'N/A') for lead in leads),
            "error": None
        }
        
    except Exception as e:
        stats = {"error": str(e)}
    
    return render_template('crm.html', stats=stats)

@app.route('/manutencao')
@login_obrigatorio()
def manutencao():
    try:
        api_url = "https://sandbox.properfy.com.br/api/property/maintenance/"
        headers = {"Authorization": "Bearer ac216f84-8e3f-4349-9ffa-884748149b89"}
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        maintenances = response.json()
        stats = {
            "total": len(maintenances),
            "by_status": Counter(maint.get('chrStatus', 'N/A') for maint in maintenances),
            "by_responsible": Counter(maint.get('responsible', 'N/A') for maint in maintenances),
            "by_category": Counter(maint.get('chrCategoryLabel', 'N/A') for maint in maintenances),
            "by_priority": Counter(maint.get('chrPriority', 'N/A') for maint in maintenances),
            "by_requester": Counter(maint.get('chrRequester', 'N/A') for maint in maintenances),
            "error": None
        }
        
        # Calculate average time
        total_seconds = 0
        completed_count = 0
        
        for maint in maintenances:
            if maint.get('dteRequest') and maint.get('dteConclusion'):
                try:
                    start = datetime.datetime.strptime(maint['dteRequest'], "%Y-%m-%dT%H:%M:%S")
                    end = datetime.datetime.strptime(maint['dteConclusion'], "%Y-%m-%dT%H:%M:%S")
                    total_seconds += (end - start).total_seconds()
                    completed_count += 1
                except:
                    continue
        
        if completed_count > 0:
            avg_seconds = total_seconds / completed_count
            stats['avg_time'] = str(datetime.timedelta(seconds=avg_seconds))
        else:
            stats['avg_time'] = "N/A"
            
    except Exception as e:
        stats = {"error": str(e)}
    
    return render_template('manutencao.html', stats=stats)

# --- Rotas do Sistema de TI ---
@app.route('/ti')
@login_obrigatorio(role=['ti_admin'])
def ti_kanban():
    tasks = carregar_dados('tasks.json')
    
    total_tasks = len(tasks)
    status_counts = Counter(t['status'] for t in tasks)
    
    chart_status_labels = list(status_counts.keys())
    chart_status_data = list(status_counts.values())
    
    responsible_counts = Counter(t['responsavel'] for t in tasks)
    chart_responsible_labels = list(responsible_counts.keys())
    chart_responsible_data = list(responsible_counts.values())
    
    priority_counts = Counter(t['prioridade'] for t in tasks)
    chart_priority_labels = list(priority_counts.keys())
    chart_priority_data = list(priority_counts.values())

    board = {
        "Backlog": [t for t in tasks if t['status'] == 'Backlog'],
        "Priorizadas": [t for t in tasks if t['status'] == 'Priorizadas'],
        "Em andamento": [t for t in tasks if t['status'] == 'Em andamento'],
        "Concluídas": [t for t in tasks if t['status'] == 'Concluídas']
    }
    
    return render_template(
        'ti_kanban.html', 
        board=board,
        total_tasks=total_tasks,
        status_counts=status_counts,
        chart_status_labels=chart_status_labels,
        chart_status_data=chart_status_data,
        chart_responsible_labels=chart_responsible_labels,
        chart_responsible_data=chart_responsible_data,
        chart_priority_labels=chart_priority_labels,
        chart_priority_data=chart_priority_data
    )

@app.route('/ti/nova_tarefa', methods=['POST'])
@login_obrigatorio(role=['ti_admin'])
def nova_tarefa_ti():
    tasks = carregar_dados('tasks.json')
    nova_task = {
        "id": len(tasks) + 1,
        "titulo": request.form['titulo'],
        "descricao": request.form['descricao'],
        "responsavel": request.form['responsavel'],
        "prioridade": request.form['prioridade'],
        "status": request.form['status'],
        "criado_por": session['username'],
        "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "notas": []
    }
    tasks.append(nova_task)
    guardar_dados(tasks, 'tasks.json')
    flash('Tarefa criada com sucesso!', 'success')
    return redirect(url_for('ti_kanban'))

@app.route('/ti/mover_tarefa', methods=['POST'])
@login_obrigatorio(role=['ti_admin'])
def mover_tarefa():
    task_id = int(request.form['task_id'])
    novo_status = request.form['novo_status']
    tasks = carregar_dados('tasks.json')
    
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = novo_status
            nota = f"Status alterado para '{novo_status}' por {session['username']} em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}."
            task.setdefault('notas', []).append(nota)
            break
    
    guardar_dados(tasks, 'tasks.json')
    return jsonify({"success": True})

@app.route('/ti/add_nota', methods=['POST'])
@login_obrigatorio(role=['ti_admin'])
def add_nota_tarefa():
    task_id = int(request.form['task_id'])
    nova_nota = request.form['nota']
    tasks = carregar_dados('tasks.json')
    
    for task in tasks:
        if task['id'] == task_id:
            nota_formatada = f"{nova_nota} (Adicionado por {session['username']} em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')})"
            task.setdefault('notas', []).append(nota_formatada)
            break
    
    guardar_dados(tasks, 'tasks.json')
    return jsonify({"success": True})

# --- Rotas de Chamados de TI ---
@app.route('/chamado_ti')
@login_obrigatorio()
def chamado_ti():
    tickets = carregar_dados('tickets.json')
    
    total_tickets = len(tickets)
    status_counts = Counter(t['status'] for t in tickets)
    
    chart_status_labels = list(status_counts.keys())
    chart_status_data = list(status_counts.values())

    chamados_por_mes = Counter(
        datetime.datetime.strptime(t['data_criacao'], "%d/%m/%Y %H:%M").strftime("%Y-%m") 
        for t in tickets
    )
    meses_ordenados = sorted(chamados_por_mes.keys())
    chart_monthly_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b/%y") for m in meses_ordenados]
    chart_monthly_data = [chamados_por_mes[m] for m in meses_ordenados]

    criadores_counts = Counter(t['criado_por'] for t in tickets)
    chart_creators_labels = list(criadores_counts.keys())
    chart_creators_data = list(criadores_counts.values())

    board = {
        "Aberto": [t for t in tickets if t['status'] == 'Aberto'],
        "Em Andamento": [t for t in tickets if t['status'] == 'Em Andamento'],
        "Concluído": [t for t in tickets if t['status'] == 'Concluído']
    }
    
    return render_template(
        'chamado_ti.html', 
        board=board, 
        user_role=session.get('role'),
        total_tickets=total_tickets,
        status_counts=status_counts,
        chart_status_labels=chart_status_labels,
        chart_status_data=chart_status_data,
        chart_monthly_labels=chart_monthly_labels,
        chart_monthly_data=chart_monthly_data,
        chart_creators_labels=chart_creators_labels,
        chart_creators_data=chart_creators_data
    )

@app.route('/chamado_ti/novo', methods=['POST'])
@login_obrigatorio()
def novo_chamado():
    tickets = carregar_dados('tickets.json')
    novo_ticket = {
        "id": len(tickets) + 1,
        "titulo": request.form['titulo'],
        "descricao": request.form['descricao'],
        "criado_por": session['username'],
        "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "Aberto",
        "notas": []
    }
    tickets.append(novo_ticket)
    guardar_dados(tickets, 'tickets.json')
    return jsonify({"success": True})

@app.route('/chamado_ti/mover', methods=['POST'])
@login_obrigatorio(role=['ti_admin'])
def mover_chamado():
    ticket_id = int(request.form['ticket_id'])
    novo_status = request.form['novo_status']
    tickets = carregar_dados('tickets.json')
    
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['status'] = novo_status
            nota = f"Status alterado para '{novo_status}' por {session['username']} em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}."
            ticket.setdefault('notas', []).append(nota)
            break
    
    guardar_dados(tickets, 'tickets.json')
    return jsonify({"success": True})

@app.route('/chamado_ti/add_nota', methods=['POST'])
@login_obrigatorio(role=['ti_admin'])
def add_nota_chamado():
    ticket_id = int(request.form['ticket_id'])
    nova_nota = request.form['nota']
    tickets = carregar_dados('tickets.json')
    
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            nota_formatada = f"{nova_nota} (Adicionado por {session['username']} em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')})"
            ticket.setdefault('notas', []).append(nota_formatada)
            break
    
    guardar_dados(tickets, 'tickets.json')
    return jsonify({"success": True})

# --- Rota Genérica ---
@app.route('/menu/<pagina>')
@login_obrigatorio()
def pagina_menu(pagina):
    flash(f'A página "{pagina.capitalize()}" será implementada em breve!', 'info')
    return redirect(url_for('admin_portal'))

if __name__ == '__main__':
    app.run(debug=True)