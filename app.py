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

def binary_search(arr, target, key=lambda x: x):
    low, high = 0, len(arr)
    while low < high:
        mid = (low + high) // 2
        if key(arr[mid]) < key(target):
            low = mid + 1
        else:
            high = mid
    return low

def bubble_sort(arr, key=lambda x: x):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if key(arr[j]) > key(arr[j+1]):
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr



#-----------------------------------------------------------------PROFESSORES------------------------------------------------------------------

@app.route('/professores')
def index():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.id, p.nome, array_agg(d.nome ORDER BY d.nome) AS disciplinas
        FROM professores p
        LEFT JOIN professor_disciplinas pd ON p.id = pd.professor_id
        LEFT JOIN disciplinas d ON pd.disciplina_id = d.id
        GROUP BY p.id, p.nome
    ''')
    professores = cur.fetchall()
    cur.close()
    conn.close()

    # Ordenar os professores por nome usando Bubble Sort
    professores = bubble_sort(professores, key=lambda x: x[1])

    return render_template('index.html', professores=professores)



@app.route('/new_professor', methods=['GET', 'POST'])
def new_professor():
    if request.method == 'POST':
        nome = request.form['nome']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO professores (nome) VALUES (%s) RETURNING id', (nome,))
            professor_id = cur.fetchone()[0]
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO professor_disciplinas (professor_id, disciplina_id) VALUES (%s, %s)', (professor_id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir o professor: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('newProfessor.html', disciplinas=disciplinas)


@app.route('/edit_professor/<int:id>', methods=['GET', 'POST'])
def edit_professor(id):
    if request.method == 'POST':
        nome = request.form['nome']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('UPDATE professores SET nome = %s WHERE id = %s', (nome, id))
            cur.execute('DELETE FROM professor_disciplinas WHERE professor_id = %s', (id,))
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO professor_disciplinas (professor_id, disciplina_id) VALUES (%s, %s)', (id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Ocorreu um erro ao editar o professor: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM professores WHERE id = %s', (id,))
        professor = cur.fetchone()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT disciplina_id FROM professor_disciplinas WHERE professor_id = %s', (id,))
        professor_disciplinas = cur.fetchall()
        professor_disciplinas_ids = [disciplina[0] for disciplina in professor_disciplinas]
        cur.close()
        conn.close()
        return render_template('editProfessor.html', professor=professor, disciplinas=disciplinas, professor_disciplinas_ids=professor_disciplinas_ids)

@app.route('/delete_professor/<int:id>', methods=['POST'])
def delete_professor(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        # Verificar se existem aulas associadas ao professor
        cur.execute('SELECT COUNT(*) FROM aulas WHERE professor_id = %s', (id,))
        count = cur.fetchone()[0]
        if count > 0:
            error = "Não é possível excluir o professor, pois existem aulas associadas a ele."
            return redirect(url_for('index', error=error))
        # Deletar as relações entre o professor e as disciplinas
        cur.execute('DELETE FROM professor_disciplinas WHERE professor_id = %s', (id,))
        # Finalmente, deletar o professor
        cur.execute('DELETE FROM professores WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        error = f"Ocorreu um erro ao deletar o professor: {e}"
        return redirect(url_for('index', error=error))



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
        # Verificar se existem aulas associadas à disciplina
        cur.execute('SELECT COUNT(*) FROM aulas WHERE disciplina_id = %s', (id,))
        count = cur.fetchone()[0]
        if count > 0:
            error = "Não é possível excluir a disciplina, pois existem aulas associadas a ela."
            return redirect(url_for('index_disciplinas', error=error))
        # Deletar as relações entre a disciplina e os professores
        cur.execute('DELETE FROM professor_disciplinas WHERE disciplina_id = %s', (id,))
        # Finalmente, deletar a disciplina
        cur.execute('DELETE FROM disciplinas WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_disciplinas'))
    except Exception as e:
        error = f"Ocorreu um erro ao deletar a disciplina: {e}"
        return redirect(url_for('index_disciplinas', error=error))


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

    cursos = bubble_sort(cursos, key=lambda x: x[1])

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
        # Verificar se existem aulas associadas ao curso
        cur.execute('SELECT COUNT(*) FROM aulas WHERE curso_id = %s', (id,))
        count = cur.fetchone()[0]
        if count > 0:
            error = "Não é possível excluir o curso, pois existem aulas associadas a ele."
            return redirect(url_for('index_curso', error=error))
        # Deletar as relações entre o curso e as disciplinas
        cur.execute('DELETE FROM curso_disciplinas WHERE curso_id = %s', (id,))
        # Finalmente, deletar o curso
        cur.execute('DELETE FROM cursos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_curso'))
    except Exception as e:
        error = f"Ocorreu um erro ao deletar o curso: {e}"
        return redirect(url_for('index_curso', error=error))


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
        sala = request.form['sala']
        periodo = request.form['periodo']
        alocacao_tipo = request.form['alocacao_tipo']

        if alocacao_tipo == 'automatica':
            message = allocate_class(curso_id, disciplina_id, professor_id, sala, periodo)
        else:
            dia_semana = request.form['dia_semana']
            hora_inicio = request.form['hora_inicio']
            hora_fim = request.form['hora_fim']
            try:
                conn = connect_db()
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO aulas (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala))
                conn.commit()
                cur.close()
                conn.close()
                message = "Aula alocada manualmente com sucesso."
            except Exception as e:
                message = f"Ocorreu um erro ao alocar a aula manualmente: {e}"

        return redirect(url_for('index_aula', message=message))
    else:
        periodo = request.args.get('periodo', 'matutino')
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM cursos')
        cursos = cur.fetchall()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT id, nome FROM professores')
        professores = cur.fetchall()
        cur.execute('''
            SELECT aulas.id, cursos.nome AS curso_nome, disciplinas.nome AS disciplina_nome, professores.nome AS professor_nome, aulas.dia_semana, aulas.hora_inicio, aulas.hora_fim, aulas.sala
            FROM aulas
            JOIN cursos ON aulas.curso_id = cursos.id
            JOIN disciplinas ON aulas.disciplina_id = disciplinas.id
            JOIN professores ON aulas.professor_id = professores.id
        ''')
        aulas = cur.fetchall()
        cur.close()
        conn.close()

        # Organizar as aulas em um dicionário para fácil acesso no template
        dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado",
                          "Domingo"]
        horario_semanal = {dia: {hora: [] for hora in range(8, 11) if periodo == 'matutino'} for dia in dias_da_semana}
        horario_semanal.update(
            {dia: {hora: [] for hora in range(19, 22) if periodo == 'noturno'} for dia in dias_da_semana})

        for aula in aulas:
            hora_inicio = aula[5].hour
            hora_fim = aula[6].hour
            for hora in range(hora_inicio, hora_fim):
                if hora in horario_semanal[aula[4]]:
                    horario_semanal[aula[4]][hora].append(aula)

        return render_template('aulas/newAula.html', cursos=cursos, disciplinas=disciplinas, professores=professores,
                               horario_semanal=horario_semanal, periodo=periodo)


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
        error = f"Ocorreu um erro ao deletar a aula: {e}"
        return redirect(url_for('index_aula', error=error))


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


def find_available_slots(horario_semanal, periodo):
    available_slots = []
    horas = range(8, 11) if periodo == 'matutino' else range(19, 22)
    dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    for dia in dias_da_semana:
        for hora in horas:
            if not horario_semanal[dia][hora]:
                pos = binary_search(available_slots, (dia, hora), key=lambda x: (dias_da_semana.index(x[0]), x[1]))
                available_slots.insert(pos, (dia, hora))

    return available_slots




def allocate_class(curso_id, disciplina_id, professor_id, sala, periodo):
    conn = connect_db()
    cur = conn.cursor()

    # Obter todas as aulas existentes
    cur.execute('''
        SELECT dia_semana, hora_inicio, hora_fim, disciplinas.nome, professores.nome, aulas.sala
        FROM aulas
        JOIN disciplinas ON aulas.disciplina_id = disciplinas.id
        JOIN professores ON aulas.professor_id = professores.id
    ''')
    aulas = cur.fetchall()

    # Organizar as aulas em um dicionário para fácil acesso
    dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    horario_semanal = {dia: {hora: [] for hora in range(8, 12)} for dia in dias_da_semana}
    for dia in dias_da_semana:
        horario_semanal[dia].update({hora: [] for hora in range(19, 23)})

    for aula in aulas:
        dia = aula[0]
        hora_inicio = aula[1].hour
        hora_fim = aula[2].hour
        for hora in range(hora_inicio, hora_fim):
            if hora in horario_semanal[dia]:
                horario_semanal[dia][hora].append({
                    'disciplina': aula[3],
                    'professor': aula[4],
                    'sala': aula[5]
                })

    # Encontrar horários disponíveis
    available_slots = find_available_slots(horario_semanal, periodo)

    if not available_slots:
        return "Não há horários disponíveis para alocar a aula."

    # Alocar a aula no primeiro horário disponível
    dia_semana, hora = available_slots[0]
    hora_inicio = f"{hora}:00"
    hora_fim = f"{hora+1}:00"

    try:
        cur.execute('''
            INSERT INTO aulas (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (curso_id, disciplina_id, professor_id, dia_semana, hora_inicio, hora_fim, sala))
        conn.commit()
    except Exception as e:
        return f"Ocorreu um erro ao alocar a aula: {e}"
    finally:
        cur.close()
        conn.close()

    return "Aula alocada com sucesso."






#-----------------------------------------------------------------AULAS------------------------------------------------------------------

@app.route('/')
def redirect_quadro_semanal():
    return redirect(url_for('quadro_semanal', periodo='noturno'))


@app.route('/quadro_semanal/<periodo>')
def quadro_semanal(periodo):
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

    # Organizar as aulas em um dicionário para fácil acesso no template
    dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    horario_semanal = {dia: {hora: [] for hora in range(24)} for dia in dias_da_semana}

    for aula in aulas:
        hora_inicio = aula[5].hour
        hora_fim = aula[6].hour
        for hora in range(hora_inicio, hora_fim):
            horario_semanal[aula[4]][hora].append(aula)

    return render_template('quadroSemanal.html', horario_semanal=horario_semanal, periodo=periodo)



if __name__ == '__main__':
    app.run(debug=True)
