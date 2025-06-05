from celery_worker import app
import json
import os
import redis
import socketio
import time

# 设置必要的环境变量
os.environ['ANN_SOCKETIO_SERVER'] = 'http://localhost:8000'
os.environ['AAN_REDIS_HOST'] = 'localhost'
os.environ['AAN_REDIS_PORT'] = '6379'
os.environ['AAN_REDIS_DB_INDEX'] = '2'

def check_dependencies():
    """检查必要的依赖是否可用"""
    # 检查 Redis
    try:
        redis_client = redis.StrictRedis(
            host=os.getenv('AAN_REDIS_HOST', 'localhost'),
            port=int(os.getenv('AAN_REDIS_PORT', 6379)),
            db=int(os.getenv('AAN_REDIS_DB_INDEX', 2))
        )
        redis_client.ping()
        print("✓ Redis connection successful")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

    # 检查 Socket.IO
    try:
        sio = socketio.Client(logger=True, engineio_logger=True)
        sio.connect(os.getenv('ANN_SOCKETIO_SERVER', 'http://localhost:8000'), namespaces=['/celery'])
        print("✓ Socket.IO connection successful")
        sio.disconnect()
    except Exception as e:
        print(f"✗ Socket.IO connection failed: {e}")
        return False

    return True

def test_summary_agent():
    # if not check_dependencies():
    #     print("Dependencies check failed. Please ensure Redis and Socket.IO server are running.")
    #     return

    # 准备测试数据
    topic = "agent-assist/test-client-001/transcript"
    message = json.dumps({
        "source": "internal",
        "text": "This is a test message for summary agent",
        "agent_id": "test_agent_001"
    })
    
    print(f"\nSending test message:")
    print(f"Topic: {topic}")
    print(f"Message: {message}")
    
    # 发送任务
    result = app.send_task(
        'aan_extensions.SummaryAgent.tasks.process_transcript',
        args=[topic, message]
    )
    
    print(f"\nTask ID: {result.id}")
    print("Task sent, waiting for result...")
    
    # 等待结果
    try:
        task_result = result.get(timeout=30)
        print(f"Task completed! Result: {task_result}")
    except Exception as e:
        print(f"Error getting result: {e}")

if __name__ == '__main__':
    test_summary_agent() 