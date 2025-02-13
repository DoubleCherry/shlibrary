# 图书馆座位预订系统

这是一个用于自动预订图书馆座位的 Python 程序。

## 功能特点

- 支持多个时间段预订
- 智能选择最佳座位
- 支持多区域预订策略
- 自动处理预订冲突
- 详细的日志记录

## 系统要求

- Python 3.11+
- Poetry 包管理器

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd testpractice
```

2. 安装依赖：
```bash
poetry install
```

## 配置说明

1. 复制配置文件模板：
```bash
cp src/apitest/config/config.yaml.example src/apitest/config/config.yaml
```

2. 编辑配置文件 `src/apitest/config/config.yaml`，填入以下信息：
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

days_ahead: 6
```

## 使用方法

1. 预订座位：
```bash
python src/apitest/main.py reserve --config ./src/apitest/config/config.yaml
```

## 座位选择策略

程序按照以下策略选择座位：

1. 优先选择已有其他用户预订的同桌座位
2. 南区优先选择奇数桌号
3. 优先选择靠右的座位
4. 按照区域优先级顺序：西区 > 东区 > 北区 > 南区

## 开发指南

### 项目结构
```
├── pyproject.toml          # Poetry 项目配置
├── src/
│   └── apitest/
│       ├── __init__.py
│       ├── main.py        # 主程序入口
│       ├── core/          # 核心功能模块
│       ├── config/        # 配置相关
│       └── utils/         # 工具函数
└── tests/                 # 测试目录
```

### 运行测试
```bash
poetry run pytest
```

## 常见问题

1. 预订失败：
   - 检查配置文件中的认证信息是否正确
   - 确认目标时间段是否可预订
   - 查看日志文件了解详细错误信息

2. 无可用座位：
   - 确认是否在预订时间窗口内
   - 检查是否有足够的剩余座位

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License 