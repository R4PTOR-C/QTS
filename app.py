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

# Quicksort function
def quicksort(arr, key=lambda x: x):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if key(x) < key(pivot)]
    middle = [x for x in arr if key(x) == key(pivot)]
    right = [x for x in arr if key(x) > key(pivot)]
    return quicksort(left, key) + middle + quicksort(right, key)

#-----------------------------------------------------------------PROFESSORES------------------------------------------------------------------

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

#-----------------------------------------------------------------DISCIPLINAS------------------------------------------------------------------

@app.route('/disciplinas')
def index_disciplinas():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM disciplinas')
    disciplinas = cur.fetchall()
    cur.close()
    conn.close()

    # Ordenar os dados pela carga horária (terceira coluna, índice 2)
    disciplinas = quicksort(disciplinas, key=lambda x: x[2])

    return render_template('disciplinas/indexDisciplina.html', disciplinas=disciplinas)

@app.route('/new_disciplina', methods=['GET', 'POST'])
def new_disciplina():
    if request.method == 'POST':
        nome = request.form['nome']
        carga_horaria = request.form['carga_horaria']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO disciplinas (nome, carga_horaria) VALUES (%s, %s)', (nome, carga_horaria))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_disciplinas'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir a disciplina: {e}")
    return render_template('disciplinas/newDisciplina.html')

@app.route('/delete_disciplina/<int:id>', methods=['POST'])
def delete_disciplina(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM disciplinas WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_disciplinas'))
    except Exception as e:
        print(f"Ocorreu um erro ao deletar o curso: {e}")
        return redirect(url_for('index_disciplinas'))

@app.route('/edit_disciplina/<int:id>', methods=['GET', 'POST'])
def edit_disciplina(id):
    if request.method == 'POST':
        nome = request.form['nome']
        carga_horaria = request.form['carga_horaria']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('UPDATE disciplinas SET nome = %s, carga_horaria = %s WHERE id = %s',
                        (nome, carga_horaria, id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_disciplinas'))
        except Exception as e:
            print(f"Ocorreu um erro ao editar a disciplina: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome, carga_horaria FROM disciplinas WHERE id = %s', (id,))
        disciplina = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('disciplinas/editDisciplina.html', disciplina=disciplina)


#-----------------------------------------------------------------CURSOS------------------------------------------------------------------

@app.route('/cursos')
def index_curso():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT cursos.id, cursos.nome, cursos.duracao, array_agg(disciplinas.nome)
        FROM cursos
        JOIN curso_disciplinas ON cursos.id = curso_disciplinas.curso_id
        JOIN disciplinas ON curso_disciplinas.disciplina_id = disciplinas.id
        GROUP BY cursos.id, cursos.nome, cursos.duracao
    ''')
    cursos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('cursos/indexCurso.html', cursos=cursos)

@app.route('/new_curso', methods=['GET', 'POST'])
def new_curso():
    if request.method == 'POST':
        nome = request.form['nome']
        duracao = request.form['duracao']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO cursos (nome, duracao) VALUES (%s, %s) RETURNING id', (nome, duracao))
            curso_id = cur.fetchone()[0]
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO curso_disciplinas (curso_id, disciplina_id) VALUES (%s, %s)', (curso_id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_curso'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir o curso: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('cursos/newCurso.html', disciplinas=disciplinas)




@app.route('/delete_curso/<int:id>', methods=['POST'])
def delete_curso(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM curso_disciplinas WHERE curso_id = %s', (id,))
        cur.execute('DELETE FROM cursos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_curso'))
    except Exception as e:
        print(f"Ocorreu um erro ao deletar o curso: {e}")
        return redirect(url_for('index_curso'))

@app.route('/edit_curso/<int:id>', methods=['GET', 'POST'])
def edit_curso(id):
    if request.method == 'POST':
        nome = request.form['nome']
        duracao = request.form['duracao']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('UPDATE cursos SET nome = %s, duracao = %s WHERE id = %s', (nome, duracao, id))
            cur.execute('DELETE FROM curso_disciplinas WHERE curso_id = %s', (id,))
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO curso_disciplinas (curso_id, disciplina_id) VALUES (%s, %s)', (id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_curso'))
        except Exception as e:
            print(f"Ocorreu um erro ao editar o curso: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome, duracao FROM cursos WHERE id = %s', (id,))
        curso = cur.fetchone()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT disciplina_id FROM curso_disciplinas WHERE curso_id = %s', (id,))
        curso_disciplinas = cur.fetchall()
        curso_disciplinas_ids = [disciplina[0] for disciplina in curso_disciplinas]
        cur.close()
        conn.close()
        return render_template('cursos/editCurso.html', curso=curso, disciplinas=disciplinas, curso_disciplinas_ids=curso_disciplinas_ids)

#-----------------------------------------------------------------AULAS------------------------------------------------------------------

@app.route('/aulas')
def index_aula():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT aulas.id, cursos.nome, disciplinas.nome, professores.nome, aulas.dia_semana, aulas.hora_inicio, aulas.hora_fim, aulas.sala
        FROM aulas
        JOIN cursos ON aulas.curso_id = cursos.id
        JOIN disciplinas ON aulas.disciplina_id = disciplinas.id
        JOIN professores ON aulas.professor_id = professores.id
    ''')
    aulas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('aulas/indexAula.html', aulas=aulas)

@app.route('/new_aula', methods=['GET', 'POST'])
def new_aula():
    if request.method == 'POST':
        curso_id = request.form['curso_id']
        disciplina_id = request.form['disciplina_id']
        professor_id = request.form['professor_id']
        dia_semana = request.form['dia_semana']
        hora_inicio = request.form['hora_inicio']
        hora_fim = request.form['hora_fim']
        sala = request.form['sala']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO aulas (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_aula'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir a aula: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM cursos')
        cursos = cur.fetchall()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT id, nome FROM professores')
        professores = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('aulas/newAula.html', cursos=cursos, disciplinas=disciplinas, professores=professores)

@app.route('/delete_aula/<int:id>', methods=['POST'])
def delete_aula(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM aulas WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_aula'))
    except Exception as e:
        print(f"Ocorreu um erro ao deletar a aula: {e}")
        return redirect(url_for('index_aula'))

@app.route('/edit_aula/<int:id>', methods=['GET', 'POST'])
def edit_aula(id):
    if request.method == 'POST':
        curso_id = request.form['curso_id']
        disciplina_id = request.form['disciplina_id']
        professor_id = request.form['professor_id']
        dia_semana = request.form['dia_semana']
        hora_inicio = request.form['hora_inicio']
        hora_fim = request.form['hora_fim']
        sala = request.form['sala']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('UPDATE aulas SET curso_id = %s, disciplina_id = %s, professor_id = %s, dia_semana = %s, hora_inicio = %s, hora_fim = %s, sala = %s WHERE id = %s',
                        (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala, id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_aula'))
        except Exception as e:
            print(f"Ocorreu um erro ao editar a aula: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala FROM aulas WHERE id = %s', (id,))
        aula = cur.fetchone()
        cur.execute('SELECT id, nome FROM cursos')
        cursos = cur.fetchall()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT id, nome FROM professores')
        professores = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('aulas/editAula.html', aula=aula, cursos=cursos, disciplinas=disciplinas, professores=professores)

if __name__ == '__main__':
    app.run(debug=True)
