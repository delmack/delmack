import json
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Inicializa a aplicação Flask
app = Flask(__name__)
# Chave secreta para gerir sessões de utilizador de forma segura
app.secret_key = 'sua_chave_secreta_aqui_pode_ser_qualquer_coisa'

def carregar_utilizadores():
    """Carrega os utilizadores do nosso 'banco de dados' JSON."""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@app.route('/')
def home():
    """Redireciona para a página de login se o utilizador não estiver autenticado."""
    if 'username' in session:
        return redirect(url_for('admin_portal'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gere a página e o processo de login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = carregar_utilizadores()
        
        # Verifica se o utilizador existe e se a password está correta
        if username in users and users[username] == password:
            session['username'] = username  # Armazena o utilizador na sessão
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_portal'))
        else:
            flash('Utilizador ou password inválidos.', 'danger')
            
    return render_template('login.html')

@app.route('/admin')
def admin_portal():
    """Página de administração, acessível apenas após o login."""
    if 'username' not in session:
        flash('Por favor, faça o login para aceder a esta página.', 'warning')
        return redirect(url_for('login'))
    
    # Passa o nome do utilizador para o template
    username = session.get('username')
    return render_template('admin.html', username=username)

@app.route('/logout')
def logout():
    """Remove o utilizador da sessão (logout)."""
    session.pop('username', None)
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('login'))

# Executa a aplicação (apenas para testes locais, o Gunicorn fará isto no Azure)
if __name__ == '__main__':
    app.run(debug=True)
