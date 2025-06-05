# Celery Test Project

这是一个使用 Celery 和 Azure Service Bus 的测试项目。

## 环境要求

- Python 3.9+
- Azure Service Bus 命名空间
- Redis (可选，用于结果后端)

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/niahZheng/celery-test.git
cd celery-test
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并设置以下变量：
```
AZURE_SERVICE_BUS_POLICY_NAME=your-policy-name
AZURE_SERVICE_BUS_KEY=your-key
AZURE_SERVICE_BUS_NAMESPACE=your-namespace
```

## 运行

1. 启动 Celery worker：
```bash
python swarmLauncher.py
```

2. 启动 Flask 应用：
```bash
python app.py
```

## 测试

1. 基本测试：
```bash
python test_celery.py
```

2. 转录测试：
```bash
python test_transcription.py
```

## 项目结构

```
celery-test/
├── aan_extensions/          # Agent 扩展
├── celery_worker.py         # Celery 配置和任务
├── app.py                   # Flask Web 应用
├── swarmLauncher.py         # Worker 启动器
├── test_celery.py          # 基本测试
├── test_transcription.py    # 转录测试
├── requirements.txt         # 项目依赖
└── README.md               # 项目文档
```

## 许可证

MIT