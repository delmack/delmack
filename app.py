from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('casamento.html')  # ou seu template

if __name__ == '__main__':
    app.run(debug=True)