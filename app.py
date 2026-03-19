from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, time
from datetime import date, timedelta

app = Flask(__name__)
CORS(app)

DATA_FILE = "tasks.json"
META_FILE = "meta.json"

def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def load_meta():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r") as f:
            return json.load(f)
    return {"streak": 0, "last_active": "", "completed_dates": []}

def save_meta(meta):
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

def update_streak():
    meta = load_meta()
    today = str(date.today())
    dates = meta.get("completed_dates", [])
    if today not in dates:
        dates.append(today)
        meta["completed_dates"] = dates
        streak = 1
        d = date.today() - timedelta(days=1)
        while str(d) in dates:
            streak += 1
            d -= timedelta(days=1)
        meta["streak"] = streak
        meta["last_active"] = today
        save_meta(meta)

# ── Tasks ──────────────────────────────────────────

@app.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = load_tasks()
    tasks.sort(key=lambda t: t.get("order", 0))
    return jsonify(tasks)

@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.json
    tasks = load_tasks()
    new_task = {
        "id": int(time.time() * 1000),
        "name": data.get("name", ""),
        "type": data.get("type", "fitness"),
        "time": data.get("time", ""),
        "dur": data.get("dur", 30),
        "pri": data.get("pri", "mid"),
        "notes": data.get("notes", ""),
        "day": data.get("day", "Mon"),
        "done": False,
        "order": len(tasks)
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return jsonify(new_task), 201

@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task.update(request.json)
            save_tasks(tasks)
            if request.json.get("done"):
                update_streak()
            return jsonify(task)
    return jsonify({"error": "Not found"}), 404

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    for i, t in enumerate(tasks):
        t["order"] = i
    save_tasks(tasks)
    return jsonify({"message": "Deleted"})

@app.route("/tasks/reorder", methods=["POST"])
def reorder_tasks():
    data = request.json
    tasks = load_tasks()
    id_map = {t["id"]: t for t in tasks}
    reordered = []
    for i, tid in enumerate(data.get("ids", [])):
        if tid in id_map:
            id_map[tid]["order"] = i
            reordered.append(id_map[tid])
    save_tasks(reordered)
    return jsonify({"message": "Reordered"})

# ── Meta / Streak ───────────────────────────────────

@app.route("/meta", methods=["GET"])
def get_meta():
    return jsonify(load_meta())

if __name__ == "__main__":
    app.run(debug=True, port=5000)
