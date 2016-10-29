from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(dir_path, 'test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

task_to_subtasks = db.Table('subtasks',
                            db.Column('subtask_id', db.Integer, db.ForeignKey('task.id')),
                            db.Column('parent_task_id', db.Integer, db.ForeignKey('task.id'))
                            )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notes = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
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


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    start = db.Column(db.DateTime, default=datetime.now)
    end = db.Column(db.DateTime, nullable=True)

    def __init__(self, start=None, end=None):
        self.start = start if start is not None else datetime.now()
        self.end = end


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
