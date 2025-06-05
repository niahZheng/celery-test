from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
import logging
from celery import Celery
from celery.signals import worker_process_init
import os
import time
import sys

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

DISABLE_TRACING = os.getenv('DISABLE_TRACING', False) == 'true'
TRACING_COLLECTOR_ENDPOINT = os.getenv('TRACING_COLLECTOR_ENDPOINT', 'jaeger')
TRACING_COLLECTOR_PORT = os.getenv('TRACING_COLLECTOR_PORT', '14268')

@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    if os.getenv("TELEMETRY", ''):
        CeleryInstrumentor().instrument()
        print("CeleryInstrumentation Enabled")
    trace.set_tracer_provider(TracerProvider())

    if DISABLE_TRACING:
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    else:
        print("JaegerExporter Enabled")
        jaeger_exporter = JaegerExporter(
            collector_endpoint=f'http://{TRACING_COLLECTOR_ENDPOINT}:{TRACING_COLLECTOR_PORT}/api/traces?format=jaeger.thrift',
        )
        span_processor = BatchSpanProcessor(jaeger_exporter)

    trace.get_tracer_provider().add_span_processor(span_processor)

# Azure Service Bus 配置
SAS_POLICY_NAME = os.getenv('AZURE_SERVICE_BUS_POLICY_NAME')
SAS_KEY = os.getenv('AZURE_SERVICE_BUS_KEY')
NAMESPACE = os.getenv('AZURE_SERVICE_BUS_NAMESPACE')

# 检查环境变量是否正确加载
print("="*50)
print("Checking Azure Service Bus Environment Variables:")
print("="*50)
print(f"AZURE_SERVICE_BUS_POLICY_NAME: {SAS_POLICY_NAME}")
print(f"AZURE_SERVICE_BUS_NAMESPACE: {NAMESPACE}")
print(f"AZURE_SERVICE_BUS_KEY: {'*' * len(SAS_KEY) if SAS_KEY else 'Not Set'}")
print("="*50)

if not all([SAS_POLICY_NAME, SAS_KEY, NAMESPACE]):
    print("ERROR: Missing required Azure Service Bus environment variables!")
    missing_vars = []
    if not SAS_POLICY_NAME: missing_vars.append('AZURE_SERVICE_BUS_POLICY_NAME')
    if not SAS_KEY: missing_vars.append('AZURE_SERVICE_BUS_KEY')
    if not NAMESPACE: missing_vars.append('AZURE_SERVICE_BUS_NAMESPACE')
    print(f"ERROR: Missing variables: {', '.join(missing_vars)}")
    print("="*50)

# 强制刷新输出缓冲区
sys.stdout.flush()

# 创建 Celery 应用
app = Celery('agent_assist_neo')

# 配置 Celery
app.conf.update(
    broker_url=f"azureservicebus://{SAS_POLICY_NAME}:{SAS_KEY}@{NAMESPACE}",
    result_backend='rpc://',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    broker_transport='azureservicebus',
    broker_transport_options={
        'queue_name': 'celery',
        'visibility_timeout': 3600,
        'wait_time_seconds': 20,
        'max_retries': 5,
        'operation_timeout': 30,
        'connection_timeout': 30,
        'socket_timeout': 30,
    }
)

# 定义测试任务
@app.task(bind=True, name='test_task')
def test_task(self, x, y):
    print(f"Processing task with x={x}, y={y}")
    time.sleep(2)  # 模拟一些处理时间
    return x + y

# 注册所有 Agent 任务
app.autodiscover_tasks(
    packages=[
        'aan_extensions.TranscriptionAgent',
        'aan_extensions.DispatcherAgent',
        'aan_extensions.NextBestActionAgent',
        'aan_extensions.CacheAgent',
        'aan_extensions.SummaryAgent'
    ],
    related_name='tasks'
)

if __name__ == '__main__':
    app.start()