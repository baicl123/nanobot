# nanobot Web Channel - 文档索引

## 📚 文档目录

本目录包含 nanobot Web Channel 的完整文档。

---

## 文档列表

### 开发指南 ⭐ 重要
1. **[CLAUDE.md](../CLAUDE.md)** - **分支管理策略和代码修改原则（必读）**
2. [development.md](./development.md) - 开发环境搭建和最佳实践

### 快速开始
3. [requirements.md](./requirements.md) - 功能需求和用户故事
4. [design.md](./design.md) - 系统设计和技术架构
5. [api.md](./api.md) - REST API 和 WebSocket API 文档
6. [database.md](./database.md) - 数据库设计和优化
7. [deployment.md](./deployment.md) - 部署指南
8. [todo.md](./todo.md) - 待办事项和已知问题

---

## 文档关系图

```
requirements.md (需求)
    ↓
design.md (设计)
    ↓
    ├─→ api.md (API 文档)
    ├─→ database.md (数据库)
    └─→ deployment.md (部署)
        ↓
development.md (开发指南)
    ↓
todo.md (任务清单)
```

---

## 按角色查看文档

### 产品经理
- [requirements.md](./requirements.md) - 了解产品需求
- [todo.md](./todo.md) - 查看开发进度

### 架构师
- [design.md](./design.md) - 系统架构设计
- [api.md](./api.md) - API 接口定义
- [database.md](./database.md) - 数据库设计

### 后端开发
- [api.md](./api.md) - API 接口文档
- [database.md](./database.md) - 数据库集成
- [development.md](./development.md) - 开发指南
- [todo.md](./todo.md) - 任务列表

### 前端开发
- [api.md](./api.md) - API 集成
- [deployment.md](./deployment.md) - 部署前端
- [development.md](./development.md) - 开发指南

### 运维工程师
- [deployment.md](./deployment.md) - 部署指南
- [api.md](./api.md) - API 健康检查

---

## 快速链接

### 常用任务

#### ⭐ 开发前必读
→ 查看 [CLAUDE.md](../CLAUDE.md) 了解分支管理和代码修改原则

#### 如何添加新 API 端点？
→ 查看 [design.md](./design.md#rest-api) 和 [api.md](./api.md)

#### 如何修改数据库 Schema？
→ 查看 [database.md](./database.md) 和 [init_db.py](../nanobot/web/init_db.py)

#### 如何部署到生产？
→ 查看 [deployment.md](./deployment.md)

#### 如何开始开发？
→ 查看 [development.md](./development.md)

#### 如何同步上游更新？
→ 查看 [CLAUDE.md](../CLAUDE.md#与上游同步)

#### 当前有哪些待办？
→ 查看 [todo.md](./todo.md)

---

## 版本历史

### v0.1.0 (2024-02-20)
- ✅ 基础 WebChannel 实现
- ✅ WebSocket 支持
- ✅ REST API
- ✅ 数据库集成
- ✅ 前端 Next.js 应用
- ✅ 基础 UI 组件
- ✅ **分支管理策略文档** - 确保可以随时同步上游更新
- ✅ **代码修改原则** - 最小化对原有代码的修改
- ✅ **配置重构** - 恢复所有原有配置，只新增 Web 相关配置

---

## 文档更新日志

| 日期 | 文档 | 更新内容 |
|------|------|----------|
| 2024-02-20 | 全部 | 初始版本 |
| 2024-02-20 | CLAUDE.md | 新增分支管理策略和代码修改原则文档 |
| 2024-02-20 | development.md | 添加分支管理策略章节 |
| 2024-02-20 | design.md | 添加开发原则章节 |
| 2024-02-20 | README.md | 添加分支管理策略快速链接 |
| 2024-02-20 | nanobot-ui/README.md | 整合项目主文档到此位置 |
| 2024-02-20 | 根 README.md | 移动到 nanobot-ui/ 目录 |

---

## 贡献

如果你发现文档有错误或需要补充，请提交 Issue 或 Pull Request。

---

## 联系方式

- 项目: https://github.com/baicl123/nanobot
- 分支: `feat/web-channel`

最后更新: 2024-02-20
