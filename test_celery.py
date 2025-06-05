from celery_worker import app, test_task
import time

@app.task(name='test_task')
def test_task(x, y):
    print(f"Processing task with x={x}, y={y}")
    time.sleep(2)  # 模拟一些处理时间
    return x + y

if __name__ == '__main__':
    # 发送一个测试任务
    result = test_task.delay(4, 4)
    print(f"Task ID: {result.id}")
    print("Task sent, waiting for result...")
    
    # 等待结果
    try:
        task_result = result.get(timeout=10)
        print(f"Task completed! Result: {task_result}")
    except Exception as e:
        print(f"Error getting result: {e}") 