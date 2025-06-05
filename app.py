from flask import Flask, request, jsonify
from celery_worker import test_task
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)

@app.route('/api/test', methods=['POST'])
def test():
    data = request.get_json()
    x = data.get('x', 0)
    y = data.get('y', 0)
    
    # 发送任务到 Celery
    task = test_task.delay(x, y)
    
    return jsonify({
        'task_id': task.id,
        'status': 'Task sent'
    })

@app.route('/api/test/<task_id>', methods=['GET'])
def get_result(task_id):
    task = test_task.AsyncResult(task_id)
    if task.ready():
        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'result': task.result
        })
    return jsonify({
        'task_id': task_id,
        'status': 'pending'
    })

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', '1') == '1'
    ) 