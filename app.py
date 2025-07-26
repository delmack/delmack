import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from collections import Counter

app = Flask(__name__)
app.secret_key = 'baggio_portal_secret_key_12345'

# --- Funções de Gestão de Dados (sem alterações) ---
def carregar_dados(ficheiro):
    try:
        with open(ficheiro, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if ficheiro == 'tickets.json' else {}

def guardar_dados(dados, ficheiro):
    with open(ficheiro, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- Rotas de Autenticação (sem alterações) ---
@app.route('/')
def home():
    if 'username' in session: return redirect(url_for('admin_portal'))
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

# --- Decorador de Login (sem alterações) ---
def login_obrigatorio(role=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'username' not in session:
                flash('Acesso negado. Por favor, faça o login.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') not in role:
                flash('Você não tem permissão para aceder a esta funcionalidade.', 'danger')
                return redirect(url_for('admin_portal'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# --- Rotas do Painel ---
@app.route('/admin')
@login_obrigatorio()
def admin_portal():
    return render_template('admin.html')

@app.route('/mapa')
@login_obrigatorio()
def mapa():
    curitiba_coords = [-25.4284, -49.2733]
    return render_template('mapa.html', default_coords=curitiba_coords)

# --- Rotas do Sistema de Chamados de TI (ATUALIZADO) ---
@app.route('/chamado_ti')
@login_obrigatorio()
def chamado_ti():
    tickets = carregar_dados('tickets.json')
    
    # --- Cálculos para os Indicadores ---
    # 1. Contadores Gerais
    total_tickets = len(tickets)
    status_counts = Counter(t['status'] for t in tickets)
    
    # 2. Gráfico de Status (Pizza)
    chart_status_labels = list(status_counts.keys())
    chart_status_data = list(status_counts.values())

    # 3. Gráfico de Chamados por Mês (Barras)
    chamados_por_mes = Counter(datetime.datetime.strptime(t['data_criacao'], "%d/%m/%Y %H:%M").strftime("%Y-%m") for t in tickets)
    # Ordenar os meses para exibição correta
    meses_ordenados = sorted(chamados_por_mes.keys())
    chart_monthly_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b/%y") for m in meses_ordenados]
    chart_monthly_data = [chamados_por_mes[m] for m in meses_ordenados]

    # 4. Gráfico de Criadores de Tickets (Donut)
    criadores_counts = Counter(t['criado_por'] for t in tickets)
    chart_creators_labels = list(criadores_counts.keys())
    chart_creators_data = list(criadores_counts.values())

    # Organiza os tickets para o quadro Kanban
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

# --- Rotas de Ações de Tickets (sem alterações) ---
@app.route('/chamado_ti/novo', methods=['POST'])
@login_obrigatorio()
def novo_chamado():
    tickets = carregar_dados('tickets.json')
    novo_ticket = {
        "id": len(tickets) + 1, "titulo": request.form['titulo'], "descricao": request.form['descricao'],
        "criado_por": session['username'], "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "Aberto", "notas": []
    }
    tickets.append(novo_ticket)
    guardar_dados(tickets, 'tickets.json')
    flash('Chamado de TI criado com sucesso!', 'success')
    return redirect(url_for('chamado_ti'))

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
    flash('Status do chamado atualizado.', 'info')
    return redirect(url_for('chamado_ti'))

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
    flash('Nota adicionada ao chamado.', 'info')
    return redirect(url_for('chamado_ti'))

# --- Rota Genérica (sem alterações) ---
@app.route('/menu/<pagina>')
@login_obrigatorio()
def pagina_menu(pagina):
    flash(f'A página "{pagina.capitalize()}" será implementada em breve!', 'info')
    return redirect(url_for('admin_portal'))

if __name__ == '__main__':
    app.run(debug=True)
