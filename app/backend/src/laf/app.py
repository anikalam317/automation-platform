from flask import Flask, jsonify, request
from flask_cors import CORS
from .models import db, Workflow, Task, Result
from .notification_listenter import NotificationListener
import threading
import psycopg2
import psycopg2.extensions


def create_app():
    app = Flask(__name__)
    app.config.from_object("laf.config.Config")
    CORS(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Initialize webhook handler
    webhook_handler = WebhookHandler(app)

    @app.route("/api/workflows", methods=["POST"])
    def create_workflow():
        data = request.get_json()
        new_workflow = Workflow()
        new_workflow.name = data["name"]
        new_workflow.status = "pending"
        db.session.add(new_workflow)
        db.session.flush()  # Get the ID without committing

        for i, task_data in enumerate(data.get("tasks", [])):
            new_task = Task()
            new_task.name = task_data["name"]
            new_task.workflow_id = new_workflow.id
            new_task.order_index = i
            new_task.status = "pending"
            db.session.add(new_task)

        db.session.commit()
        return jsonify({"id": new_workflow.id, "name": new_workflow.name}), 201

    @app.route("/api/workflows", methods=["GET"])
    def get_workflows():
        workflows = Workflow.query.order_by(Workflow.created_at.desc()).all()
        output = []
        for w in workflows:
            tasks = []
            for t in sorted(w.tasks, key=lambda x: x.order_index):
                results = [{"id": r.id, "data": r.data} for r in t.results]
                tasks.append(
                    {
                        "id": t.id,
                        "name": t.name,
                        "instrument": t.instrument,
                        "status": t.status,
                        "order_index": t.order_index,
                        "results": results,
                    }
                )
            output.append(
                {"id": w.id, "name": w.name, "status": w.status, "tasks": tasks}
            )
        return jsonify(output)

    @app.route("/api/workflows/<int:workflow_id>", methods=["PUT"])
    def update_workflow(workflow_id):
        workflow = Workflow.query.get_or_404(workflow_id)
        data = request.get_json()

        if "status" in data:
            workflow.status = data["status"]
        if "name" in data:
            workflow.name = data["name"]

        db.session.commit()
        return jsonify({"message": "Workflow updated"}), 200

    @app.route("/api/tasks/<int:task_id>", methods=["PUT"])
    def update_task(task_id):
        task = Task.query.get_or_404(task_id)
        data = request.get_json()

        if "status" in data:
            task.status = data["status"]
        if "results" in data:
            new_result = Result()
            new_result.task_id = task.id
            new_result.data = data["results"]
            db.session.add(new_result)

        db.session.commit()
        return jsonify({"message": "Task updated"}), 200

    @app.route("/api/webhook/task/update", methods=["POST"])
    def webhook_task_update():
        data = request.get_json()
        task = Task.query.get(data["task_id"])
        if not task:
            return jsonify({"error": "Task not found"}), 404

        task.status = data["status"]
        if "results" in data:
            new_result = Result()
            new_result.task_id = task.id
            new_result.data = data["results"]
            db.session.add(new_result)

        db.session.commit()
        return jsonify({"message": "Task updated"}), 200

    # Start the database listener in a separate thread
    def start_db_listener():
        webhook_handler.start_listener()

    listener_thread = threading.Thread(target=start_db_listener, daemon=True)
    listener_thread.start()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
