from flask import Flask, render_template_string, request, redirect, url_for
import json, os, threading

app = Flask(__name__)
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

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Админ Панель</title>
<meta charset="utf-8">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
    <div class="container">
        <h1>🛠 Админ Панель (Порт 5001)</h1>
        <hr>
        <div class="row">
            <div class="col-md-6">
                <div class="card p-3 mb-3">
                    <h3>Создать тест</h3>
                    <form method="POST" action="/create_test">
                        <input type="text" name="title" class="form-control" placeholder="Название теста" required>
                        <button type="submit" class="btn btn-primary mt-2">Создать</button>
                    </form>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card p-3 mb-3">
                    <h3>Добавить вопрос</h3>
                    <form method="POST" action="/add_question">
                        <select name="test_id" class="form-select mb-2" required>
                            <option value="">Выберите тест...</option>
                            {% for test in data.tests %}
                            <option value="{{ test.id }}">{{ test.title }}</option>
                            {% endfor %}
                        </select>
                        <input type="text" name="text" class="form-control mb-2" placeholder="Текст вопроса" required>
                        <input type="text" name="ans1" class="form-control mb-1" placeholder="Ответ 1" required>
                        <input type="text" name="ans2" class="form-control mb-1" placeholder="Ответ 2" required>
                        <input type="text" name="ans3" class="form-control mb-2" placeholder="Ответ 3" required>
                        <label>Правильный ответ:</label>
                        <select name="correct" class="form-select mb-2">
                            <option value="0">Ответ 1</option>
                            <option value="1">Ответ 2</option>
                            <option value="2">Ответ 3</option>
                        </select>
                        <button type="submit" class="btn btn-success">Добавить вопрос</button>
                    </form>
                </div>
            </div>
        </div>

        <h3>📊 Трекинг прохождений</h3>
        <table class="table table-striped bg-white">
            <thead>
                <tr>
                    <th>IP</th><th>Тест</th><th>Вопрос #</th>
                    <th>✅</th><th>❌</th><th>Статус</th>
                </tr>
            </thead>
            <tbody>
                {% for attempt in data.attempts[::-1] %}
                <tr>
                    <td>{{ attempt.ip }}</td>
                    <td>{{ attempt.test_title }}</td>
                    <td>{{ attempt.q_index + 1 }}</td>
                    <td class="text-success">{{ attempt.correct }}</td>
                    <td class="text-danger">{{ attempt.wrong }}</td>
                    <td>{% if attempt.finished %}Завершен{% else %}В процессе{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="mt-4 p-3 bg-white border rounded">
            <h5 class="text-danger">⚠️ Зона очистки</h5>
            <form method="POST" action="/clear_attempts" onsubmit="return confirm('Вы уверены? Это удалит всю статистику прохождений!');">
                <button type="submit" class="btn btn-danger">🗑 Очистить всю статистику IP</button>
            </form>
        </div>
        
        <a href="/" class="btn btn-outline-dark mt-3">Обновить</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = load_data()
    return render_template_string(ADMIN_HTML, data=data)

@app.route('/create_test', methods=['POST'])
def create_test():
    data = load_data()
    test_id = len(data['tests']) + 1
    data['tests'].append({"id": test_id, "title": request.form.get('title'), "questions": []})
    save_data(data)
    return redirect('/')

@app.route('/add_question', methods=['POST'])
def add_question():
    data = load_data()
    test_id = int(request.form.get('test_id'))
    for test in data['tests']:
        if test['id'] == test_id:
            q_id = len(test['questions']) + 1
            test['questions'].append({
                "id": q_id,
                "text": request.form.get('text'),
                "answers": [
                    {"text": request.form.get('ans1'), "correct": int(request.form.get('correct')) == 0},
                    {"text": request.form.get('ans2'), "correct": int(request.form.get('correct')) == 1},
                    {"text": request.form.get('ans3'), "correct": int(request.form.get('correct')) == 2}
                ]
            })
            break
    save_data(data)
    return redirect('/')

@app.route('/clear_attempts', methods=['POST'])
def clear_attempts():
    data = load_data()
    data['attempts'] = []  # Очищаем только попытки, тесты остаются
    save_data(data)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
