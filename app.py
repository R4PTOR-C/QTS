from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

import psycopg2

app = Flask(__name__)
Bootstrap(app)

def connect_db():
    return psycopg2.connect(
        dbname='qts_db',
        user='rafael',
        password='7rFqVx4mP2F9f0XAFKvvIbn0835Yz7xd',
        host='dpg-coofaqol5elc739o5gj0-a.oregon-postgres.render.com',
        port='5432'
    )

@app.route('/')
def index():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM professores')
    professores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', professores=professores)

@app.route('/new_professor', methods=['GET', 'POST'])
def new_professor():
    if request.method == 'POST':
        nome = request.form['nome']
        disciplina = request.form['disciplina']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO professores (nome, disciplina) VALUES (%s, %s)', (nome, disciplina))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir o professor: {e}")
    return render_template('new.html')

@app.route('/disciplinas')
def indexDisciplinas():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM disciplinas')
    disciplinas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', disciplinas=disciplinas)

# Adicione outras rotas e handlers conforme necessário

if __name__ == '__main__':
    app.run(debug=True)
