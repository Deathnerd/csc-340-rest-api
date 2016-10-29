from datetime import datetime

import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from utils import CustomJSONEncoder

app = Flask(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(dir_path, 'test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

app.json_encoder = CustomJSONEncoder

task_to_subtasks = db.Table('subtasks',
                            db.Column('subtask_id', db.Integer, db.ForeignKey('task.id')),
                            db.Column('parent_task_id', db.Integer, db.ForeignKey('task.id'))
                            )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notes = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=False)
    subtasks = db.relationship('Task',
                               secondary=task_to_subtasks,
                               primaryjoin=(task_to_subtasks.c.parent_task_id == id),
                               secondaryjoin=(task_to_subtasks.c.subtask_id == id),
                               backref='parent_task',
                               lazy='dynamic'
                               )
    time_entries = db.relationship('TimeEntry', backref='task', lazy='dynamic')

    def __init__(self, description, notes=None):
        self.description = description
        self.notes = notes

    def serialize(self):
        return {
            "id": self.id,
            "notes": self.notes,
            "description": self.description,
            "subtasks": [subtask.serialize() for subtask in self.subtasks],
            "time_entries": [entry.serialize() for entry in self.time_entries]
        }


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    start = db.Column(db.DateTime, default=datetime.now)
    end = db.Column(db.DateTime, nullable=True)

    def __init__(self, start=None, end=None):
        self.start = start if start is not None else datetime.now()
        self.end = end

    def stop(self):
        self.end = datetime.now()

    def serialize(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "start": self.start,
            "end": self.end
        }


@app.route('/task/all', methods=["GET"])
def get_all_tasks():
    return jsonify(task.serialize() for task in Task.query.all())


@app.route('/task/<int:id>', methods=["GET"])
def get_task_by_id(id):
    task = Task.query.get_or_404(id)
    return jsonify(task.serialize())


@app.route('/task', methods=["POST"])
def post_single_task():
    if not request.json or len(request.json) == 0:
        return jsonify(error="No JSON supplied"), 400
    j = request.json
    if not j.get('description', None):
        return jsonify(error="Description required for all new Task objects"), 400
    new_task = Task(j['description'], j.get('notes', None))
    if j.get('parent_task_id', None) is not None:
        parent_task = Task.query.get(j['parent_task_id'])
        if parent_task is None:
            return jsonify(error="No parent task with id of {} found".format(j['parent_task_id'])), 400
        parent_task.subtasks.append(new_task)
        db.session.add(parent_task)
    db.session.add(new_task)
    db.session.commit()

    return jsonify(new_task.serialize())


@app.route('/task/<int:id>', methods=["DELETE"])
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify(message="Task {} deleted".format(id), success=True)


@app.route('/task/<int:id>', methods=["PATCH"])
def update_single_task(id):
    if not request.json or len(request.json) == 0:
        return jsonify(error="No JSON supplied"), 400
    task = Task.query.get_or_404(id)
    j = request.json
    if j.get('description', None) is None:
        return jsonify(error="Description required for all Task objects"), 400

    task.description = j.get("description", "")
    task.notes = j.get("notes", None)

    db.session.add(task)
    db.session.commit()

    return jsonify(task.serialize())


@app.route('/task/running', methods=["GET"])
def get_started_tasks():
    running_time_entries = TimeEntry.query.filter_by(end=None).all()
    return jsonify(
        task.serialize() for task in Task.query.filter(Task.id.in_(t.id for t in running_time_entries)).all())


@app.route('/task/stopped', methods=["GET"])
def get_stopped_tasks():
    stopped_time_entries = TimeEntry.query.filter(TimeEntry.end.isnot(None)).all()
    return jsonify(
        task.serialize() for task in Task.query.filter(Task.id.in_(t.id for t in stopped_time_entries)).all())


@app.route('/task/<int:id>/timeentries', methods=["GET"])
def get_time_entries_for_task(id):
    task = Task.query.get_or_404(id)
    return jsonify(entry.serialize() for entry in task.time_entries)


@app.route('/task/<int:id>/start', methods=["POST"])
def start_new_time_entry_for_task(id):
    task = Task.query.get_or_404(id)
    if any(t.end is None for t in task.time_entries):
        return jsonify(error="Task {} already started".format(id)), 400
    time_entry = TimeEntry()
    task.time_entries.append(time_entry)
    db.session.add(task)
    db.session.add(time_entry)
    db.session.commit()
    return jsonify(time_entry.serialize())


@app.route('/task/<int:id>/stop', methods=["POST"])
def stop_task(id):
    task = Task.query.get_or_404(id)
    if len(task.time_entries) == 0 or all(t.end is not None for t in task.time_entries):
        return jsonify(error="Task {} is not started".format(id)), 400
    last_time_entry = task.time_entries[-1]
    last_time_entry.stop()
    db.session.add(task)
    db.session.commit()
    return jsonify(last_time_entry.serialize())


@app.route('/timeentry/<int:id>', methods=["GET"])
def get_single_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    return jsonify(time_entry.serialize())


@app.route("/timeentry/<int:id>", methods=["DELETE"])
def delete_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    db.session.delete(time_entry)
    db.session.commit()
    return jsonify(message="Time Entry {} removed successfully".format(id), success=True)


@app.route('/timeentry/<int:id>/task', methods=['GET'])
def get_task_for_time_entry(id):
    time_entry = TimeEntry.query.get_or_404(id)
    task = Task.query.get_or_404(time_entry.task_id)
    return jsonify(task.serialize())


@app.route('/timeentry/stopped', methods=['GET'])
def get_stopped_time_entries():
    return jsonify(entry.serialize() for entry in TimeEntry.query.filter(TimeEntry.end.isnot(None)).all())


@app.route('/timeentry/stopped/<int:task_id>', methods=["GET"])
def get_stopped_time_entries_for_task(task_id):
    return jsonify(entry.serialize() for entry in
                   TimeEntry.query.filter(TimeEntry.end.isnot(None) and TimeEntry.task_id == task_id).all())


@app.route('/timeentry/running', methods=['GET'])
def get_running_time_entries():
    return jsonify(entry.serialize() for entry in TimeEntry.query.filter(TimeEntry.end.is_(None)).all())


@app.route('/timeentry/running/<int:task_id>', methods=['GET'])
def get_running_time_entries_for_task(task_id):
    return jsonify(entry.serialize() for entry in
                   TimeEntry.query.filter(TimeEntry.end.is_(None) and TimeEntry.task_id == task_id).all())


@app.route('/timeentry/<int:id>/stop', methods=["POST"])
def stop_time_entry_by_id(id):
    time_entry = TimeEntry.query.get_or_404(id)
    time_entry.stop()
    db.session.add(time_entry)
    db.session.commit()
    return jsonify(time_entry.serialize())


@app.route('/timeentry/<int:id>/start/<int:timestamp>', methods=["PATCH"])
def update_start_of_time_entry(id, timestamp):
    time_entry = TimeEntry.query.get_or_404(id)
    time_entry.start = datetime.fromtimestamp(timestamp)
    db.session.add(time_entry)
    db.session.commit()
    return jsonify(time_entry.serialize())


@app.route('/timeentry/<int:id>/end/<int:timestamp>', methods=["PATCH"])
def update_end_of_time_entry(id, timestamp):
    time_entry = TimeEntry.query.get_or_404(id)
    time_entry.end = datetime.fromtimestamp(timestamp)
    db.session.add(time_entry)
    db.session.commit()
    return jsonify(time_entry.serialize())


if __name__ == '__main__':
    app.run(debug=True, port=9000)
