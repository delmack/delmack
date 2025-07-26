import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'baggio_portal_secret_key_12345'

# --- Funções de Gestão de Dados ---

def carregar_dados(ficheiro):
    """Carrega dados de um ficheiro JSON."""
    try:
        with open(ficheiro, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if ficheiro == 'tickets.json' else {}

def guardar_dados(dados, ficheiro):
    """Guarda dados num ficheiro JSON."""
    with open(ficheiro, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- Rotas Principais e Autenticação ---

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
            session['role'] = user_data['role'] # Armazena o perfil do utilizador
            return redirect(url_for('admin_portal'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada com segurança.', 'info')
    return redirect(url_for('login'))

# --- Rotas do Painel de Administração ---

def login_obrigatorio(role=None):
    """Decorador para verificar se o utilizador está logado e tem o perfil necessário."""
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

@app.route('/admin')
@login_obrigatorio()
def admin_portal():
    return render_template('admin.html', username=session.get('username'))

# --- Rota do Mapa ---

@app.route('/mapa')
@login_obrigatorio()
def mapa():
    # Coordenadas de Curitiba, PR
    curitiba_coords = [-25.4284, -49.2733]
    return render_template('mapa.html', default_coords=curitiba_coords)

# --- Rotas do Sistema de Chamados de TI ---

@app.route('/chamado_ti')
@login_obrigatorio()
def chamado_ti():
    tickets = carregar_dados('tickets.json')
    # Organiza os tickets por status para o quadro Kanban
    board = {
        "Aberto": [t for t in tickets if t['status'] == 'Aberto'],
        "Em Andamento": [t for t in tickets if t['status'] == 'Em Andamento'],
        "Concluído": [t for t in tickets if t['status'] == 'Concluído']
    }
    return render_template('chamado_ti.html', board=board, user_role=session.get('role'))

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

# --- Rota Genérica para Menus Futuros ---

@app.route('/menu/<pagina>')
@login_obrigatorio()
def pagina_menu(pagina):
    flash(f'A página "{pagina.capitalize()}" será implementada em breve!', 'info')
    return redirect(url_for('admin_portal'))

if __name__ == '__main__':
    app.run(debug=True)
