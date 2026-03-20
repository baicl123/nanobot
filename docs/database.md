# nanobot Web Channel - 数据库设计文档

## 数据库选择

### 为什么选择 seekdb？

- **MySQL 兼容**: 完全兼容 MySQL 协议和 SQL 语法
- **全文搜索**: 内置 FULLTEXT 索引，支持中文分词（ngram parser）
- **向量能力**: 支持向量列，未来可扩展语义搜索
- **高性能**: 支持 ACID 事务和高并发
- **易部署**: Docker 一键启动
- **管理界面**: Web 界面（http://localhost:2886）

## 部署 seekdb

### Docker 启动

```bash
docker run -d \
  -p 2881:2881 \
  -p 2886:2886 \
  -e ROOT_PASSWORD="seekdb" \
  oceanbase/seekdb
```

**端口说明**:
- `2881`: 数据库连接端口
- `2886`: Web 管理界面

### 连接测试

```bash
# 使用 MySQL 客户端
mysql -h127.0.0.1 -P2881 -uroot -pseekdb

# 或使用 curl
curl http://localhost:2886
```

## 数据库 Schema

### 数据库创建

```sql
CREATE DATABASE IF NOT EXISTS nanobot;
USE nanobot;
```

### 表结构

#### 1. 会话表 (conversations)

存储用户会话信息。

```sql
CREATE TABLE IF NOT EXISTS conversations (
    -- 主键
    id VARCHAR(64) PRIMARY KEY COMMENT '会话ID (UUID)',

    -- 用户信息
    user_id VARCHAR(255) NOT NULL COMMENT '用户ID',
    channel VARCHAR(50) NOT NULL COMMENT '渠道: web/telegram/whatsapp等',

    -- 会话属性
    title VARCHAR(500) NOT NULL DEFAULT '新对话' COMMENT '会话标题',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 统计
    message_count INT DEFAULT 0 COMMENT '消息数量',

    -- 扩展字段
    metadata JSON COMMENT '元数据',

    -- 索引
    INDEX idx_user_updated (user_id, updated_at DESC),
    INDEX idx_channel (channel)
) COMMENT='会话表';
```

**字段说明**:

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | VARCHAR(64) | 会话唯一标识（UUID）| PRIMARY KEY |
| user_id | VARCHAR(255) | 用户 ID | idx_user_updated |
| channel | VARCHAR(50) | 渠道标识 | idx_channel |
| title | VARCHAR(500) | 会话标题（Agent 或用户生成）| - |
| created_at | TIMESTAMP | 创建时间 | - |
| updated_at | TIMESTAMP | 更新时间（自动更新）| idx_user_updated |
| message_count | INT | 消息数量（用于统计和排序）| - |
| metadata | JSON | 扩展元数据 | - |

**索引说明**:
- `PRIMARY KEY`: id - 快速查找单个会话
- `idx_user_updated`: (user_id, updated_at) - 用户会话列表查询（按时间倒序）
- `idx_channel`: channel - 按渠道筛选会话

---

#### 2. 消息表 (messages)

存储会话中的所有消息。

```sql
CREATE TABLE IF NOT EXISTS messages (
    -- 主键
    id VARCHAR(64) PRIMARY KEY COMMENT '消息ID (UUID)',

    -- 关联
    conversation_id VARCHAR(64) NOT NULL COMMENT '会话ID',

    -- 消息内容
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    content TEXT NOT NULL COMMENT '消息内容',

    -- 扩展字段
    metadata JSON COMMENT '元数据',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_conversation_created (conversation_id, created_at),
    FULLTEXT INDEX ft_content (content) WITH (parser='ngram'),

    -- 外键
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE
) COMMENT='消息表';
```

**字段说明**:

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | VARCHAR(64) | 消息唯一标识（UUID）| PRIMARY KEY |
| conversation_id | VARCHAR(64) | 所属会话 ID | idx_conversation_created, FOREIGN KEY |
| role | ENUM | 消息角色 | - |
| content | TEXT | 消息内容（支持长文本）| FULLTEXT |
| metadata | JSON | 扩展元数据（如 token 数、模型版本等）| - |
| created_at | TIMESTAMP | 创建时间 | idx_conversation_created |

**索引说明**:
- `PRIMARY KEY`: id - 快速查找单条消息
- `idx_conversation_created`: (conversation_id, created_at) - 查询会话消息（按时间正序）
- `ft_content`: FULLTEXT - 全文搜索（使用 ngram 分词器支持中文）
- `FOREIGN KEY`: conversation_id -> conversations(id) - 级联删除

**级联删除**:
当会话被删除时，该会话的所有消息会自动删除。

---

## 索引优化

### 复合索引设计

#### 用户会话列表查询
```sql
-- 查询：获取用户的会话列表（按更新时间倒序）
SELECT * FROM conversations
WHERE user_id = 'user_123'
ORDER BY updated_at DESC
LIMIT 50;

-- 使用索引：idx_user_updated
```

#### 会话消息查询
```sql
-- 查询：获取会话的消息（按时间正序）
SELECT * FROM messages
WHERE conversation_id = 'conv_123'
ORDER BY created_at ASC
LIMIT 100;

-- 使用索引：idx_conversation_created
```

### 全文索引设计

```sql
-- ngram 分词器配置
-- 支持中文分词，适合短语搜索

-- 查询示例
SELECT * FROM messages
WHERE MATCH(content) AGAINST('Python 编程' IN NATURAL LANGUAGE MODE);
```

**搜索模式**:
- `IN NATURAL LANGUAGE MODE`: 自然语言模式（默认）
- `IN BOOLEAN MODE`: 布尔模式（支持 + - 操作符）
- `WITH QUERY EXPANSION`: 查询扩展（相关词扩展）

---

## 数据访问层设计

### Repository 模式

```python
# nanobot/web/repositories/conversation_repo.py
class ConversationRepository:
    """会话数据访问层"""

    async def create(self, user_id: str, title: str, channel: str) -> dict:
        """
        创建会话

        返回: {
            "id": "uuid",
            "user_id": "user_123",
            "title": "新对话",
            "channel": "web",
            "message_count": 0
        }
        """

    async def get_by_user(self, user_id: str, limit: int) -> list[dict]:
        """
        获取用户会话列表

        参数:
            user_id: 用户 ID
            limit: 最大返回数量（默认 50）

        返回: [
            {
                "id": "uuid",
                "title": "会话1",
                "created_at": "2024-02-20T10:00:00Z",
                "updated_at": "2024-02-20T10:30:00Z",
                "message_count": 15
            },
            ...
        ]
        """

    async def get(self, conversation_id: str) -> dict | None:
        """获取单个会话"""

    async def update_title(self, conversation_id: str, title: str) -> bool:
        """更新会话标题"""

    async def increment_count(self, conversation_id: str) -> bool:
        """增加消息计数"""

    async def delete(self, conversation_id: str) -> bool:
        """删除会话（级联删除消息）"""

    async def exists(self, conversation_id: str) -> bool:
        """检查会话是否存在"""
```

### 连接池管理

```python
# nanobot/web/database.py
class Database:
    """数据库连接池"""

    def __init__(self, host, port, user, password, db, pool_size=10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.pool_size = pool_size  # 最大连接数
        self.pool: aiomysql.Pool = None

    async def create_pool(self):
        """创建连接池"""
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            minsize=5,       # 最小连接数
            maxsize=self.pool_size,
            autocommit=False,
            charset='utf8mb4'
        )

    @asynccontextmanager
    async def get_connection(self):
        """获取连接（上下文管理器）"""
        async with self.pool.acquire() as conn:
            yield conn
```

**连接池配置**:
- 最小连接数: 5
- 最大连接数: 10（可配置）
- 字符集: utf8mb4（支持 Emoji 和多语言）
- 自动提交: 关闭（手动控制事务）

---

## 数据库初始化

### 初始化脚本

```bash
# 运行初始化
cd /Users/white/dev/github/nanobot
python -m nanobot.web.init_db init

# 查看表
python -m nanobot.web.init_db show

# 重置表（危险操作！）
python -m nanobot.web.init_db drop
python -m nanobot.web.init_db init
```

### 验证安装

```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE conversations;
DESCRIBE messages;

-- 查看索引
SHOW INDEX FROM conversations;
SHOW INDEX FROM messages;

-- 查看外键
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'nanobot'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

---

## SQL 查询示例

### 常用查询

#### 获取用户最新会话
```sql
SELECT id, title, message_count, updated_at
FROM conversations
WHERE user_id = 'user_123'
ORDER BY updated_at DESC
LIMIT 10;
```

#### 获取会话消息
```sql
SELECT id, role, content, created_at
FROM messages
WHERE conversation_id = 'conv_123'
ORDER BY created_at ASC
LIMIT 50;
```

#### 统计用户消息数
```sql
SELECT
    c.id,
    c.title,
    COUNT(m.id) as total_messages
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE c.user_id = 'user_123'
GROUP BY c.id, c.title;
```

#### 全文搜索
```sql
SELECT
    m.id,
    m.content,
    m.role,
    c.title,
    c.id as conversation_id
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
WHERE c.user_id = 'user_123'
AND MATCH(m.content) AGAINST('Python' IN NATURAL LANGUAGE MODE)
ORDER BY m.created_at DESC
LIMIT 20;
```

---

## 数据迁移

### 备份

```bash
# 使用 Docker exec 备份
docker exec nanobot-seekdb mysql -uroot -pseekdb nanobot > backup_$(date +%Y%m%d).sql

# 或使用 mysqldump
docker exec nanobot-seekdb mysqldump -uroot -pseekdb nanobot > backup.sql
```

### 恢复

```bash
# 恢复备份
docker exec -i nanobot-seekdb mysql -uroot -pseekdb nanobot < backup.sql
```

### 清空数据

```sql
-- 删除所有消息（保留会话）
TRUNCATE TABLE messages;

-- 删除所有会话（级联删除消息）
TRUNCATE TABLE conversations;

-- 删除所有数据
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE messages;
TRUNCATE TABLE conversations;
SET FOREIGN_KEY_CHECKS = 1;
```

---

## 性能优化

### 查询优化建议

1. **使用索引**: 确保查询使用索引
   ```sql
   -- 使用 EXPLAIN 分析查询
   EXPLAIN SELECT * FROM conversations WHERE user_id = 'user_123';
   ```

2. **限制返回数量**: 使用 LIMIT 避免返回过多数据
   ```sql
   SELECT * FROM messages WHERE conversation_id = 'conv_123' LIMIT 100;
   ```

3. **分页查询**: 使用 OFFSET 实现分页
   ```sql
   SELECT * FROM conversations
   WHERE user_id = 'user_123'
   ORDER BY updated_at DESC
   LIMIT 20 OFFSET 0;   -- 第 1 页
   LIMIT 20 OFFSET 20;  -- 第 2 页
   ```

4. **避免 SELECT ***: 只选择需要的列
   ```sql
   -- 不推荐
   SELECT * FROM conversations;

   -- 推荐
   SELECT id, title, updated_at FROM conversations;
   ```

### 慢查询日志

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 记录超过 1 秒的查询

-- 查看慢查询日志
SHOW VARIABLES LIKE 'slow_query_log%';
```

---

## 监控和维护

### 健康检查

```python
# nanobot/web/database.py
async def health_check(self) -> bool:
    """检查数据库连接"""
    try:
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                return result is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

### 定期维护

```sql
-- 分析表
ANALYZE TABLE conversations;
ANALYZE TABLE messages;

-- 优化表
OPTIMIZE TABLE conversations;
OPTIMIZE TABLE messages;

-- 检查表
CHECK TABLE conversations;
CHECK TABLE messages;
```

---

## 未来扩展

### 向量搜索（Phase 3）

```sql
-- 添加向量列
ALTER TABLE messages ADD COLUMN content_vector VECTOR(1536) COMMENT '内容向量';

-- 创建向量索引（HNSW）
ALTER TABLE messages ADD INDEX idx_vector (content_vector);

-- 混合检索（全文 + 向量）
SELECT *,
  DOT_PRODUCT(content_vector,_embedding) as similarity
FROM messages
WHERE MATCH(content) AGAINST('Python' IN NATURAL LANGUAGE MODE)
ORDER BY similarity DESC
LIMIT 10;
```

### 分区表（大量数据）

```sql
-- 按时间分区
ALTER TABLE messages
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### 读写分离

```python
# 配置主从数据库
class Database:
    def __init__(self, master_config, slave_configs):
        self.master = await create_pool(master_config)  # 写库
        self.slaves = [await create_pool(c) for c in slave_configs]  # 读库

    @asynccontextmanager
    async def get_connection(self, read_only=False):
        if read_only:
            # 随机选择一个从库
            conn = random.choice(self.slaves).acquire()
        else:
            # 使用主库
            conn = self.master.acquire()
        yield conn
```
