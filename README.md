# 图书馆座位预订系统

这是一个自动化的图书馆座位预订系统，提供 API 服务和命令行工具，支持多用户、多时段的座位预订功能。

## 功能特点

- 支持多用户并发预订
- 灵活的区域优先级配置
- 自动化的座位预订流程
- RESTful API 接口
- 命令行工具支持
- 详细的日志记录
- Docker 容器化部署

## 技术栈

- Python 3.10+
- FastAPI
- Pydantic
- Poetry
- Docker
- Click
- Loguru
- PyYAML

## 安装

### 使用 Poetry 安装

```bash
# 克隆项目
git clone <repository-url>
cd testpractice

# 安装依赖
poetry install
```

### 使用 Docker 安装

```bash
# 构建镜像
docker build -t apitest .

# 运行容器
docker run -d -p 8000:8000 apitest
```

## 配置

系统使用 YAML 格式的配置文件，配置文件示例：

```yaml
users:
  - name: "用户名"
    headers:
      clientId: "你的客户端ID"
      source: "1"
      accessToken: "你的访问令牌"
      sign: "你的签名"
      timestamp: "时间戳"
      Cookie: "你的Cookie"

api:
  base_url: "https://yuyue.library.sh.cn"
  floor_id: "4"
  library_id: "1"
  seat_reservation_type: "2"
  period_reservation_type: "14"

area_priority:
  - "西"
  - "东"
  - "北"
  - "南"

logging:
  level: "INFO"
  rotation: "1 day"
  retention: "7 days"
  encoding: "utf-8"

reservation:
  days_ahead: 6

users:
  - name: "用户1"
    headers:
      Cookie: "your-cookie-here"
  - name: "用户2"
    headers:
      Cookie: "another-cookie-here"
```

## 使用方法

### API 服务

启动 API 服务：

```bash
# 使用 Poetry
poetry run python -m apitest.main serve

# 或者直接使用 Python
python -m apitest.main serve

# 指定主机和端口
python -m apitest.main serve --host 0.0.0.0 --port 8000
```

### 命令行工具

执行座位预订：

```bash
# 使用指定配置文件预订
python -m apitest.main reserve --config config.yaml

# 指定预订日期
python -m apitest.main reserve --config config.yaml --date 2024-03-20

# 设置日志级别
python -m apitest.main reserve --config config.yaml --log-level DEBUG
```

验证配置文件：

```bash
python -m apitest.main validate --config config.yaml
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 项目结构

```
├── pyproject.toml          # 项目依赖配置
├── poetry.lock            # 依赖版本锁定
├── src/
│   └── apitest/
│       ├── __init__.py
│       ├── main.py        # 主入口
│       ├── api/           # API 相关
│       ├── core/          # 核心业务逻辑
│       ├── config/        # 配置管理
│       ├── schemas/       # 数据模型
│       └── utils/         # 工具函数
└── tests/                 # 测试用例
```

### 运行测试

```bash
poetry run pytest
```

## 许可证

[MIT License](LICENSE)

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。 