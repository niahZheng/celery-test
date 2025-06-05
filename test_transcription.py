from celery_worker import app
import json
import os
import socketio
import time

# 设置必要的环境变量
os.environ['ANN_SOCKETIO_SERVER'] = 'http://localhost:8000'

def check_socketio():
    """检查 Socket.IO 服务器是否可用"""
    try:
        sio = socketio.Client(logger=True, engineio_logger=True)
        sio.connect(os.getenv('ANN_SOCKETIO_SERVER', 'http://localhost:8000'), namespaces=['/celery'])
        print("✓ Socket.IO connection successful")
        sio.disconnect()
        return True
    except Exception as e:
        print(f"✗ Socket.IO connection failed: {e}")
        return False

def test_transcription_agent():
    # if not check_socketio():
    #     print("Socket.IO server check failed. Please ensure Socket.IO server is running.")
    #     return

    # 准备测试数据
    topic = "agent-assist/test-client-001/transcript"
    message = json.dumps({
        "source": "internal",
        "text": "This is a test message for transcription agent",
        "agent_id": "test_agent_001"
    })
    
    print(f"\nSending test message:")
    print(f"Topic: {topic}")
    print(f"Message: {message}")
    
    # 发送任务
    result = app.send_task(
        'aan_extensions.TranscriptionAgent.tasks.process_transcript',
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
    test_transcription_agent() 