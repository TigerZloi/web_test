from flask import Flask, render_template_string, request, redirect, url_for, session
import json, os, threading, uuid

app = Flask(__name__)
app.secret_key = 'simple_secret_key_ubuntu'
DATA_FILE = 'data.json'
lock = threading.Lock()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tests": [], "attempts": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with lock:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

CLIENT_HTML = """
<!DOCTYPE html>
<html>
<head><title>Тестирование</title>
<meta charset="utf-8">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4 bg-white">
    <div class="container" style="max-width: 600px;">
        <h1 class="mb-4">📝 Доступные тесты</h1>
        <div class="list-group">
            {% for test in data.tests %}
            <a href="/start/{{ test.id }}" class="list-group-item list-group-item-action">
                {{ test.title }} <span class="badge bg-primary">{{ test.questions|length }} вопр.</span>
            </a>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

TEST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Вопрос</title>
<meta charset="utf-8">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4 bg-light">
    <div class="container" style="max-width: 600px;">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">Вопрос {{ attempt.q_index + 1 }} из {{ total }}</div>
            <div class="card-body">
                <h4 class="mb-4">{{ question.text }}</h4>
                <form method="POST" action="/answer">
                    {% for answer in question.answers %}
                    <div class="form-check mb-3 p-3 border rounded">
                        <input class="form-check-input" type="radio" name="answer_idx" value="{{ loop.index0 }}" id="a{{ loop.index0 }}" required>
                        <label class="form-check-label w-100" for="a{{ loop.index0 }}">{{ answer.text }}</label>
                    </div>
                    {% endfor %}
                    <button type="submit" class="btn btn-primary w-100">Ответить</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head><title>Результат</title>
<meta charset="utf-8">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4 text-center bg-light">
    <div class="container">
        <div class="card shadow p-5">
            <h1 class="text-success">✅ Тест завершен!</h1>
            <p>IP: <b>{{ attempt.ip }}</b></p>
            <h3>Правильно: {{ attempt.correct }}</h3>
            <p class="text-danger">Ошибок: {{ attempt.wrong }}</p>
            <a href="/" class="btn btn-outline-primary mt-3">Вернуться</a>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = load_data()
    return render_template_string(CLIENT_HTML, data=data)

@app.route('/start/<int:test_id>')
def start_test(test_id):
    data = load_data()
    test = next((t for t in data['tests'] if t['id'] == test_id), None)
    if not test: return redirect('/')
    ip = request.remote_addr
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    attempt = {"session_id": session_id, "ip": ip, "test_id": test_id, "test_title": test['title'], "q_index": 0, "correct": 0, "wrong": 0, "finished": False}
    data['attempts'].append(attempt)
    save_data(data)
    return redirect('/question')

@app.route('/question')
def question():
    session_id = session.get('session_id')
    if not session_id: return redirect('/')
    data = load_data()
    attempt = next((a for a in data['attempts'] if a['session_id'] == session_id), None)
    if not attempt or attempt['finished']: return redirect('/result')
    test = next((t for t in data['tests'] if t['id'] == attempt['test_id']), None)
    if attempt['q_index'] >= len(test['questions']):
        attempt['finished'] = True
        save_data(data)
        return redirect('/result')
    question = test['questions'][attempt['q_index']]
    return render_template_string(TEST_HTML, question=question, attempt=attempt, total=len(test['questions']))

@app.route('/answer', methods=['POST'])
def answer():
    session_id = session.get('session_id')
    if not session_id: return redirect('/')
    data = load_data()
    attempt = next((a for a in data['attempts'] if a['session_id'] == session_id), None)
    test = next((t for t in data['tests'] if t['id'] == attempt['test_id']), None)
    if attempt and test:
        q = test['questions'][attempt['q_index']]
        ans_idx = int(request.form.get('answer_idx'))
        if q['answers'][ans_idx]['correct']:
            attempt['correct'] += 1
        else:
            attempt['wrong'] += 1
        attempt['q_index'] += 1
        save_data(data)
    return redirect('/question')

@app.route('/result')
def result():
    session_id = session.get('session_id')
    if not session_id: return redirect('/')
    data = load_data()
    attempt = next((a for a in data['attempts'] if a['session_id'] == session_id), None)
    return render_template_string(RESULT_HTML, attempt=attempt)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
