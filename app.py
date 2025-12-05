# app.py
from flask import Flask, request, jsonify, send_from_directory, render_template
import json, os
from datetime import datetime, timedelta
from nlp.parser import parse_event
from threading import Lock

EVENTS_FILE = os.path.join('data', 'events.json')
LOCK = Lock()
app = Flask(__name__, static_folder='static', template_folder='templates')

def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []

    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            data = f.read().strip()
            if not data:
                return []
            return json.loads(data)

    except json.JSONDecodeError:
        # file bị hỏng → reset
        save_events([])
        return []



def save_events(events):
    with LOCK:
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse_text():
    text = request.json.get('text', '')
    now = datetime.now()
    parsed = parse_event(text, now=now)
    if 'location' in parsed and parsed['location'] is None:
        parsed['location'] = ""
    return jsonify(parsed)

@app.route('/events', methods=['GET','POST','PUT','DELETE'])
def events():
    if request.method == 'GET':
        return jsonify(load_events())

    events = load_events()

    if request.method == 'POST':
        data = request.json
        events.append(data)
        save_events(events)
        return jsonify({'ok': True})

    if request.method == 'PUT':
        # expects data contains index or id, here simple index
        data = request.json
        idx = data.get('index')
        if idx is None:
            return jsonify({'error':'missing index'}), 400
        events[idx] = data['event']
        save_events(events)
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        idx = int(request.args.get('index', -1))
        if 0 <= idx < len(events):
            events.pop(idx)
            save_events(events)
            return jsonify({'ok': True})
        return jsonify({'error': 'bad index'}), 400

@app.route('/export', methods=['GET'])
def export_file():
    # serve the JSON file from the data directory
    return send_from_directory('data', os.path.basename(EVENTS_FILE), as_attachment=True)

@app.route('/import', methods=['POST'])
def import_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error':'no file'}), 400
    content = json.load(file)
    save_events(content)
    return jsonify({'ok': True})

# endpoint to return reminders due within next interval
@app.route('/due_reminders', methods=['GET'])
def due_reminders():
    now = datetime.now()
    events = load_events()
    due = []
    for idx, e in enumerate(events):
        st = e.get('start_time')
        rem = e.get('reminder_minutes', 0) or 0
        if not st:
            continue
        try:
            dt = datetime.fromisoformat(st)
            remind_at = dt - timedelta(minutes=int(rem))
            if now <= remind_at <= now + timedelta(seconds=65):
                due.append({'index': idx, 'event': e})
        except Exception as ex:
            continue
    return jsonify(due)

if __name__ == '__main__':
    # ensure events file exists
    if not os.path.exists(EVENTS_FILE):
        save_events([])
    app.run(debug=True)
