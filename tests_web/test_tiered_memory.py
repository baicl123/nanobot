#!/usr/bin/env python3
"""测试两层记忆系统"""

import asyncio
import tempfile
import shutil
from pathlib import Path

# 测试数据库层
async def test_database_layer():
    """测试数据库基础功能"""
    print("\n=== 测试数据库层 ===")

    from nanobot.db.sqlite import SQLiteDatabase

    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"

    try:
        # 初始化数据库
        db = SQLiteDatabase(db_path)
        await db.connect()

        # 健康检查
        is_healthy = await db.health_check()
        print(f"✓ 数据库健康检查: {is_healthy}")

        # 测试基本SQL执行
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT 1 as test")
            result = await cursor.fetchone()
            print(f"✓ 基本SQL执行: {result}")

        await db.disconnect()
        print("✓ 数据库层测试通过")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


async def test_migrations():
    """测试数据库迁移"""
    print("\n=== 测试数据库迁移 ===")

    from nanobot.db.sqlite import SQLiteDatabase
    from nanobot.db.migrations import run_migrations, get_current_version, MIGRATIONS

    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"

    try:
        db = SQLiteDatabase(db_path)
        await db.connect()

        # 运行迁移
        async with db.get_connection() as conn:
            await run_migrations(conn)

            # 检查版本
            version = await get_current_version(conn)
            print(f"✓ 数据库版本: {version}")

            # 检查表是否创建
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in await cursor.fetchall()]
            print(f"✓ 创建的表: {tables}")

            # 验证 user_memories 表结构
            cursor = await conn.execute("PRAGMA table_info(user_memories)")
            columns = await cursor.fetchall()
            print(f"✓ user_memories 表列: {[c[1] for c in columns]}")

            # 验证 session_memories 表结构
            cursor = await conn.execute("PRAGMA table_info(session_memories)")
            columns = await cursor.fetchall()
            print(f"✓ session_memories 表列: {[c[1] for c in columns]}")

        await db.disconnect()
        print("✓ 迁移测试通过")

    finally:
        shutil.rmtree(temp_dir)


async def test_user_memory_repository():
    """测试用户记忆 Repository"""
    print("\n=== 测试用户记忆 Repository ===")

    from nanobot.db.sqlite import SQLiteDatabase
    from nanobot.db.repositories.user_memory import UserMemoryRepository
    from nanobot.db.migrations import run_migrations

    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"

    try:
        db = SQLiteDatabase(db_path)
        await db.connect()

        # 运行迁移
        async with db.get_connection() as conn:
            await run_migrations(conn)

        # 初始化 Repository
        user_repo = UserMemoryRepository(temp_dir, db)

        # 测试创建用户记忆
        user_id = "test_user_001"
        content = """# 用户记忆

## 偏好
- 喜欢用 Python 编程
- 习惯在晚上 10 点后工作

## 术语
- "项目A" 指的是考勤系统
"""
        await user_repo.update_user_memory(user_id, content)
        print(f"✓ 创建用户记忆: {user_id}")

        # 测试读取用户记忆
        retrieved = await user_repo.get_user_memory(user_id)
        assert retrieved == content, "内容不匹配"
        print(f"✓ 读取用户记忆: {len(retrieved)} 字符")

        # 测试更新用户记忆
        new_content = content + "\n## 新增\n- 喜欢喝咖啡"
        await user_repo.update_user_memory(user_id, new_content)
        print(f"✓ 更新用户记忆")

        # 测试获取记忆上下文
        context = await user_repo.get_memory_context(user_id)
        assert "用户记忆" in context
        print(f"✓ 获取记忆上下文: {len(context)} 字符")

        # 测试文件系统备份
        backup_file = temp_dir / "memory" / "users" / user_id / "MEMORY.md"
        assert backup_file.exists(), "备份文件不存在"
        backup_content = backup_file.read_text()
        assert "喜欢喝咖啡" in backup_content
        print(f"✓ 文件系统备份: {backup_file}")

        # 测试不存在的用户
        empty = await user_repo.get_user_memory("non_existent")
        assert empty == "", "不存在的用户应返回空字符串"
        print(f"✓ 不存在的用户返回空")

        await db.disconnect()
        print("✓ 用户记忆 Repository 测试通过")

    finally:
        shutil.rmtree(temp_dir)


async def test_session_memory_repository():
    """测试会话记忆 Repository"""
    print("\n=== 测试会话记忆 Repository ===")

    from nanobot.db.sqlite import SQLiteDatabase
    from nanobot.db.repositories.session_memory import SessionMemoryRepository
    from nanobot.db.migrations import run_migrations

    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"

    try:
        db = SQLiteDatabase(db_path)
        await db.connect()

        # 运行迁移
        async with db.get_connection() as conn:
            await run_migrations(conn)

        # 初始化 Repository
        session_repo = SessionMemoryRepository(temp_dir, db)

        # 测试创建会话记忆
        session_id = "web:test_user:conv-001"
        content = """这段对话讨论了考勤查询功能。用户询问如何查看 10 月份的考勤记录，
AI 提供了按日期筛选的 SQL 查询语句。用户还询问了导出考勤数据为 Excel 的方法。"""
        await session_repo.update_session_memory(session_id, content, message_count=10)
        print(f"✓ 创建会话记忆: {session_id}")

        # 测试读取会话记忆
        retrieved = await session_repo.get_session_memory(session_id)
        assert "考勤查询" in retrieved
        print(f"✓ 读取会话记忆: {len(retrieved)} 字符")

        # 测试更新会话记忆
        new_content = content + "\n\n新增：用户询问了数据导出功能。"
        await session_repo.update_session_memory(session_id, new_content, message_count=15)
        print(f"✓ 更新会话记忆")

        # 测试获取用户的活跃会话
        # 创建更多会话
        await session_repo.update_session_memory("web:test_user:conv-002", "第二个会话", 5)
        await session_repo.update_session_memory("web:other_user:conv-001", "其他用户的会话", 3)

        active_sessions = await session_repo.get_active_sessions("test_user")
        print(f"✓ 用户的活跃会话数: {len(active_sessions)}")
        for sess in active_sessions:
            print(f"  - {sess['session_id']}: {sess['message_count']} 条消息")

        # 测试文件系统备份
        backup_file = temp_dir / "memory" / "sessions" / session_id / "SUMMARY.md"
        assert backup_file.exists(), "备份文件不存在"
        print(f"✓ 文件系统备份: {backup_file}")

        await db.disconnect()
        print("✓ 会话记忆 Repository 测试通过")

    finally:
        shutil.rmtree(temp_dir)


async def test_tiered_memory_manager():
    """测试两层记忆管理器"""
    print("\n=== 测试两层记忆管理器 ===")

    from nanobot.agent.tiered_memory import TieredMemoryManager

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 初始化管理器
        manager = TieredMemoryManager(temp_dir)
        await manager.initialize()
        print("✓ TieredMemoryManager 初始化成功")

        # 测试用户记忆
        user_id = "60079031"
        user_content = "# 用户偏好\n- 喜欢用 Python\n- 喜欢简洁的代码"
        await manager.consolidate_to_user_memory(user_id, "用户在讨论中提到了偏好 Python")
        print(f"✓ 合并到用户记忆: {user_id}")

        user_context = await manager.get_user_context(user_id)
        assert "Python" in user_context
        print(f"✓ 获取用户上下文: {len(user_context)} 字符")

        # 测试会话记忆
        session_id = "web:60079031:conv-001"
        session_summary = "讨论了 Python 异步编程的最佳实践"
        await manager.update_session_summary(session_id, session_summary, message_count=20)
        print(f"✓ 更新会话摘要: {session_id}")

        retrieved_summary = await manager.get_session_summary(session_id)
        assert "异步编程" in retrieved_summary
        print(f"✓ 获取会话摘要: {len(retrieved_summary)} 字符")

        # 测试数据库文件创建
        db_file = temp_dir / "nanobot.db"
        assert db_file.exists(), "数据库文件不存在"
        print(f"✓ 数据库文件: {db_file}")

        # 测试文件系统备份
        user_backup = temp_dir / "memory" / "users" / user_id / "MEMORY.md"
        assert user_backup.exists(), "用户记忆备份不存在"
        print(f"✓ 用户记忆备份: {user_backup}")

        session_backup = temp_dir / "memory" / "sessions" / session_id / "SUMMARY.md"
        assert session_backup.exists(), "会话记忆备份不存在"
        print(f"✓ 会话记忆备份: {session_backup}")

        await manager.close()
        print("✓ TieredMemoryManager 测试通过")

    finally:
        shutil.rmtree(temp_dir)


async def test_session_key_parsing():
    """测试 session_key 解析"""
    print("\n=== 测试 Session Key 解析 ===")

    # 测试新的 session_key 格式
    test_cases = [
        ("web:60079031:conv-001", "60079031", "conv-001"),
        ("web:user123:conversation-abc", "user123", "conversation-abc"),
        ("web:test:123", "test", "123"),
    ]

    for session_key, expected_user, expected_session in test_cases:
        parts = session_key.split(':', 2)
        if len(parts) == 3:
            user_id = parts[1]
            session_id = parts[2]
            assert user_id == expected_user, f"用户ID不匹配: {user_id} != {expected_user}"
            assert session_id == expected_session, f"会话ID不匹配: {session_id} != {expected_session}"
            print(f"✓ {session_key} -> user_id={user_id}, session_id={session_id}")

    print("✓ Session Key 解析测试通过")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试两层记忆系统")
    print("=" * 60)

    tests = [
        test_database_layer,
        test_migrations,
        test_user_memory_repository,
        test_session_memory_repository,
        test_tiered_memory_manager,
        test_session_key_parsing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"\n✗ 测试失败: {test.__name__}")
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
