### GET /task/all
Returns all tasks in the database. The structure is as follows:
```json
[
  {
      "id": 1,
      "description": "A task description",
      "notes": "The notes for a task",
      "subtasks": [
          {
              "id": 3,
              "description": "This is a subtask",
              "notes": "This is the notes for a subtask",
              "subtasks": [],
              "time_entries": []
          }
      ],
      "time_entries": [
          {
              "id": 1,
              "task_id": 1,
              "start": 1477784579,
              "end": 1477984579
          },
          {
              "id": 2,
              "task_id": 1,
              "start": 1478784579,
              "end": null
          }
      ]
  }
]
```
### GET /task/{id}
Returns a task object identified by the given integer ID. If the task cannot be found, a 404 error code will be sent

### GET /task/running
Returns a list of all running task objects. Started tasks are tasks whose `end` property is null

### GET /task/stopped
Returns a list of all stopped task objects. Stopped tasks are tasks whos `end` property is not null

### GET /task/{id}/timeentries
Returns a list of all time entries for a task with the given integer id. If a task cannot be found, a 404 error code will be sent.

### POST /task/{id}/start
Starts a new time entry for the given task. If the task is already in a "running" state, then a 400 error code will be sent with a JSON object that has an error message in it. Otherwise, the new time entry object is sent

### POST /task/{id}/stop
Stops a task. If the task is not in a "running" state, then a 400 error code is sent with a JSON object that has an error message in it. Otherwise, the updated time entry object is sent

### PATCH /task/{id}
Allows a task to be updated via a JSON input which is as follows:
```json
{
  "description": "The new description",
  "notes": "The new notes"
}
```
Note: A description _IS REQUIRED_ for all task objects.

This is admittedly limited and is intentionally done so because this API is as simple as you can get.


### POST /task
Allows making a new task via the same mechanism as the above PATCH method: JSON input. The expected input is as follows:
```json
{
  "description": "The new task's description",
  "notes": "The new task's notes"
}
```
Note: A description _IS REQUIRED_ for all task object.

### DELETE /task/{id}
Deletes a task via a its integer id. If a task cannot be found by that ID, a 404 error code is returned. When the task has been successfully deleted, a JSON structure is returned with a message stating so and a `success` property set to true.

### GET /timeentry/{id}
Returns a time entry by its integer id. If a time entry cannot be found by that ID, a 404 error code is returned.

### GET /timeentry/{id}/task
Returns the task for a given time entry id. If the time entry cannot be found, then a 404 error code is returned.

### GET /timeentry/stopped
Returns a list of all stopped time entries. A stopped time entry is a time entry whose `end` property is not null.

### GET /timeentry/running
Returns a list of all running time entries. A running time entry is a time entry whose `end` property is null.

### GET /timeentry/stopped/{task_id}
Returns a list of all stopped time entries for a given task identified by its (the task's) integer ID. A stopped time entry is one whose `end` property is not null

### GET /timeentry/running/{task_id}
Returns a list of all running time entries for a given task identified by its (the task's) integer ID. A running time entry is one whose `end` property is null

### POST /timeentry/{id}/stop
Stops a time entry given by its integer id. If the time entry cannot be found, a 404 error code will be returned. If it is found, the `end` property is updated and the updated (stopped) time entry object is returned as JSON

### PATCH /timeentry/{id}/start/{timestamp}
Updates a given time entry's `start` property identified by its integer id to the given UNIX timestamp value. If the time entry cannot be found, a 404 error code is returned. Otherwise the `start` property of the time entry is updated and the updated time entry object is returned as JSON.

### PATCH /timeentry/{id}/end/{timestamp}
Updates a given time entry's `end` property identified by its integer id to the given UNIX timestamp value. If the time entry cannot be found, a 404 error code is returned. Otherwise the `end` property of the time entry is updated and the updated time entry object is returned as JSON.
