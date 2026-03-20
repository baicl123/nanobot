# nanobot Web Channel - 开发指南

## 分支管理策略

### 重要原则

本项目采用严格的分支管理策略，**主分支（main）只用于同步上游官方更新，不进行开发**。

### Main 分支
- **用途**：与官方 nanobot 仓库保持同步
- **原则**：
  - 只用于合并上游更新
  - 不进行任何开发工作
  - 保持与官方仓库一致
- **更新方式**：
  ```bash
  git checkout main
  git fetch upstream
  git merge upstream/main
  git checkout feat/web-channel
  git merge main
  ```

### Feat/web-channel 分支
- **用途**：Web Channel 功能开发分支
- **修改原则**：
  1. **新增代码**：不受限制，可以自由添加新文件和新功能
  2. **修改代码**：只有在必要时才修改原有代码
  3. **删除代码**：禁止删除任何原有代码、配置或功能
- **必要修改判断标准**：
  - 是否绝对必要？
  - 能否通过其他方式实现（如扩展、继承、组合）？
  - 是否影响现有功能？
  - 是否有更优雅的方案？

### 代码审查清单

提交代码前必须确认：
- [ ] 我是否删除了任何原有代码？
- [ ] 我的修改是否影响了现有功能？
- [ ] 这个修改是否可以通过新增代码实现？
- [ ] 我是否测试了其他频道仍然正常工作？
- [ ] 我是否添加了必要的注释说明修改原因？

### 已知的必要修改

以下修改被认为是必要且合理的：

1. **nanobot/config/schema.py**
   - 新增 `WebConfig` 类
   - 新增 `DatabaseConfig` 类
   - 修改 `ChannelsConfig` 类（添加 `web` 字段）
   - 修改 `Config` 类（添加 `database` 字段）

2. **nanobot/channels/manager.py**
   - 添加 Web Channel 初始化代码

3. **pyproject.toml**
   - 添加依赖：fastapi, uvicorn, aiomysql

### 禁止的修改

- 删除任何配置类或字段
- 删除任何频道初始化代码
- 删除任何依赖库
- 修改现有频道的核心逻辑
- 修改基础类（除非绝对必要）

详见：[CLAUDE.md](../CLAUDE.md)

---

## 开发环境搭建

### 1. 克隆仓库

```bash
# 后端
git clone https://github.com/baicl123/nanobot.git
cd nanobot
git checkout feat/web-channel

# 前端
git clone https://github.com/baicl123/nanobot-ui.git
cd nanobot-ui
```

### 2. Python 虚拟环境

```bash
cd /Users/white/dev/github/nanobot

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e .
```

### 3. Node.js 环境

```bash
cd /Users/white/dev/github/nanobot-ui

# 安装依赖
npm install

# 安装 TypeScript 类型
npm run type-check
```

### 4. 启动开发服务

**后端**:
```bash
cd /Users/white/dev/github/nanobot
source venv/bin/activate
nanobot gateway
```

**前端**:
```bash
cd /Users/white/dev/github/nanobot-ui
npm run dev
```

### 5. 启动数据库

```bash
# 方式 1: Docker Compose
docker-compose up -d seekdb

# 方式 2: 直接运行
docker run -d -p 2881:2881 -p 2886:2886 -e ROOT_PASSWORD="seekdb" oceanbase/seekdb
```

---

## 项目结构

### 后端结构

```
nanobot/
├── nanobot/
│   ├── channels/
│   │   ├── base.py              # BaseChannel 抽象类
│   │   ├── manager.py           # ChannelManager
│   │   └── web.py               # WebChannel 实现 ⭐
│   ├── web/                     # FastAPI 应用 ⭐
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI 主应用
│   │   ├── database.py          # 数据库连接池
│   │   ├── init_db.py           # 数据库初始化脚本
│   │   ├── schemas.py           # Pydantic 数据模型
│   │   ├── repositories/        # 数据访问层
│   │   │   ├── conversation_repo.py
│   │   │   └── message_repo.py
│   │   └── routes/              # API 路由
│   │       ├── conversations.py
│   │       ├── messages.py
│   │       └── search.py
│   ├── config/
│   │   └── schema.py            # 配置模型（WebConfig, DatabaseConfig）
│   ├── bus/
│   │   └── events.py            # 消息事件
│   └── session/
│       └── manager.py           # SessionManager
├── docs/                        # 文档 ⭐
│   ├── requirements.md
│   ├── design.md
│   ├── api.md
│   ├── database.md
│   ├── deployment.md
│   ├── development.md
│   └── todo.md
├── pyproject.toml               # 项目配置
└── README.md
```

### 前端结构

```
nanobot-ui/
├── app/                         # Next.js App Router
│   ├── globals.css              # 全局样式
│   ├── layout.tsx               # 根布局
│   └── page.tsx                 # 主页面
├── components/
│   ├── chat/                    # 聊天组件
│   │   └── ChatArea.tsx
│   ├── sidebar/                 # 侧边栏组件
│   │   └── Sidebar.tsx
│   ├── ui/                      # UI 组件库
│   │   ├── avatar.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── scroll-area.tsx
│   └── theme-provider.tsx
├── lib/
│   ├── store/                   # Zustand 状态管理
│   │   ├── conversation-store.ts
│   │   ├── message-store.ts
│   │   ├── ui-store.ts
│   │   └── index.ts
│   ├── types.ts                 # TypeScript 类型
│   ├── utils.ts                 # 工具函数
│   └── websocket.ts            # WebSocket 客户端
├── docs/                        # 文档 ⭐
│   ├── requirements.md
│   ├── design.md
│   ├── components.md
│   ├── state-management.md
│   ├── api-integration.md
│   ├── styling.md
│   ├── development.md
│   └── todo.md
├── public/                      # 静态资源
├── .env.local                   # 环境变量
├── next.config.js               # Next.js 配置
├── tailwind.config.ts           # Tailwind CSS 配置
├── tsconfig.json                # TypeScript 配置
├── package.json
└── README.md
```

---

## 编码规范

### Python (后端)

**代码风格**:
- 遵循 PEP 8
- 使用 ruff 进行格式化: `ruff check nanobot/`
- 最大行长度: 100 字符

**类型注解**:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager

async def create_conversation(
    user_id: str,
    title: str = "新对话",
    channel: str = "web"
) -> dict:
    """创建新会话."""
    ...
```

**文档字符串**:
```python
async def get_conversation(conversation_id: str) -> dict | None:
    """
    获取单个会话。

    Args:
        conversation_id: 会话 ID

    Returns:
        会话数据，不存在时返回 None

    Raises:
        HTTPException: 会话不存在时抛出 404
    """
    ...
```

### TypeScript (前端)

**代码风格**:
- 使用 ESLint: `npm run lint`
- 使用 Prettier 格式化
- 单引号
- 2 空格缩进

**类型定义**:
```typescript
// 优先使用 interface
interface Conversation {
  id: string;
  title: string;
  channel: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// 联合类型使用 type
type MessageRole = 'user' | 'assistant' | 'system';

// 泛型使用
function useState<S>(initialState: S | (() => S)): [S, Dispatch<SetStateAction<S>>];
```

**命名约定**:
- 组件: PascalCase (ChatArea.tsx)
- 工具函数: camelCase (formatDate)
- 常量: UPPER_SNAKE_CASE (MAX_MESSAGE_LENGTH)
- 接口: PascalCase (Conversation)
- 类型别名: PascalCase (MessageRole)

---

## 测试

### 后端测试

**单元测试**:
```bash
cd /Users/white/dev/github/nanobot

# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_web_channel.py

# 覆盖率报告
pytest --cov=nanobot/web --cov-report=html
```

**示例测试**:
```python
# tests/test_web_channel.py
import pytest
from nanobot.channels.web import WebChannel
from nanobot.config.schema import WebConfig

@pytest.fixture
def web_config():
    return WebConfig(
        enabled=True,
        host="127.0.0.1",
        port=8765
    )

@pytest.mark.asyncio
async def test_webchannel_start(web_config):
    channel = WebChannel(web_config, ...)
    await channel.start()
    assert channel.is_running
    await channel.stop()
```

### 前端测试

**单元测试** (计划中):
```bash
cd /Users/white/dev/github/nanobot-ui

# 运行测试
npm test

# 覆盖率
npm run test:coverage
```

---

## 调试技巧

### 后端调试

**使用日志**:
```python
from loguru import logger

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

**断点调试**:
```bash
# 使用 pdb
python -m pdb -m nanobot.web.init_db init

# 使用 VS Code debugger
# 在 launch.json 中配置:
{
  "name": "Python: Current File",
  "type": "debugpy",
  "request": "launch",
  "program": "${file}",
  "console": "integratedTerminal"
}
```

**API 测试**:
```bash
# 使用 wscat 测试 WebSocket
wscat -c "ws://localhost:8765/ws/test-session"

# 使用 curl 测试 REST API
curl http://localhost:8765/health
curl http://localhost:8765/api/conversations?user_id=test_user
```

### 前端调试

**浏览器控制台**:
```javascript
// 查看 WebSocket 消息
ws.addEventListener('message', (event) => {
  console.log('Received:', JSON.parse(event.data));
});

// 查看状态
import { useConversationStore } from '@/lib/store';
const store = useConversationStore();
console.log(store.getState());
```

**React DevTools**:
- 安装 React DevTools 浏览器扩展
- 查看组件树和状态

**网络调试**:
- 浏览器 DevTools -> Network -> WS
- 查看 WebSocket 帧

---

## 常见开发任务

### 添加新的 API 端点

1. 定义 Pydantic Schema (`nanobot/web/schemas.py`)
2. 创建 Repository 方法 (`nanobot/web/repositories/`)
3. 添加路由处理函数 (`nanobot/web/routes/`)
4. 注册路由到 FastAPI app (`nanobot/web/app.py`)

### 添加新的 WebSocket 消息类型

1. 更新 WebSocket 消息处理逻辑 (`nanobot/channels/web.py`)
2. 添加消息类型定义 (`nanobot/web/schemas.py`)
3. 更新前端 WebSocket 客户端 (`nanobot-ui/lib/websocket.ts`)

### 修改数据库 Schema

1. 更新 `nanobot/web/init_db.py`
2. 运行迁移: `python -m nanobot.web.init_db init`
3. 更新 Repository 方法

### 添加新的前端组件

1. 创建组件文件
2. 使用 shadcn/ui 组件作为基础
3. 添加到页面中

---

## Git 工作流

### 分支策略

```
main (upstream)
  ↑
  │ (merge)
  │
feat/web-channel (开发分支)
```

**工作流程**:
1. 从 `feat/web-channel` 创建功能分支
2. 开发和测试
3. 提交到 `feat/web-channel`
4. 定期合并 `main` 的更新到 `feat/web-channel`

### 提交规范

```bash
# 格式: <type>: <subject>

# 类型:
# feat: 新功能
# fix: 修复 bug
# docs: 文档更新
# refactor: 重构
# test: 测试
# chore: 构建/工具链

# 示例:
git commit -m "feat: add message search API"
git commit -m "fix: handle WebSocket disconnect gracefully"
git commit -m "docs: update deployment guide"
```

---

## 性能分析

### 后端性能分析

```python
# 使用 cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... 执行代码 ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### 前端性能分析

```bash
# 生产构建分析
npm run build

# 查看包大小
npm run build -- --analyze

# 使用 Lighthouse
npx lighthouse http://localhost:3000 --view
```

---

## 热重载

### 后端热重载

使用 `--reload` 参数:
```bash
uvicorn nanobot.web.app:app --reload --host 0.0.0.0 --port 8765
```

或集成到 WebChannel 启动逻辑中。

### 前端热重载

Next.js 自带热重载，`npm run dev` 自动启用。

---

## 代码审查清单

### 后端 PR Checklist

- [ ] 代码符合 PEP 8 规范
- [ ] 所有函数有类型注解
- [ ] 所有公共函数有文档字符串
- [ ] 添加了单元测试
- [ ] 测试覆盖率 > 80%
- [ ] 数据库操作使用参数化查询
- [ ] 错误处理完善
- [ ] 日志记录适当
- [ ] 更新了文档

### 前端 PR Checklist

- [ ] 代码符合 ESLint 规范
- [ ] 组件有 PropTypes 或 TypeScript 类型
- [ ] 状态管理正确使用
- [ ] 无 `any` 类型（除非必要）
- [ ] 响应式设计测试
- [ ] 浏览器兼容性测试
- [ ] 更新了文档

---

## 有用的资源

### 文档链接
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [WebSocket MDN 文档](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Next.js 文档](https://nextjs.org/docs)
- [Zustand 文档](https://zustand-demo.pmnd.rs/)

### 工具链接
- [seekdb 官方文档](https://www.oceanbase.com/docs)
- [shadcn/ui 组件库](https://ui.shadcn.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)

---

## 获取帮助

### 报告 Bug
1. 在 GitHub 上创建 Issue
2. 描述问题和重现步骤
3. 附上日志和错误信息

### 功能请求
1. 在 GitHub 上创建 Issue
2. 标记为 `enhancement`
3. 描述使用场景

### 代码贡献
1. Fork 仓库
2. 创建功能分支
3. 提交 Pull Request
4. 等待代码审查
