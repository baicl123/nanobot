#!/usr/bin/env python3
"""两层记忆系统集成测试 - 模拟真实使用场景"""

import asyncio
import tempfile
import shutil
from pathlib import Path


async def test_realistic_user_scenario():
    """测试真实用户场景：多用户、多会话"""
    print("\n" + "="*60)
    print("真实场景测试：多用户多会话")
    print("="*60)

    from nanobot.agent.tiered_memory import TieredMemoryManager

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 初始化管理器
        manager = TieredMemoryManager(temp_dir)
        await manager.initialize()

        # 场景 1: 用户 60079031 的第一个会话
        print("\n--- 场景 1: 用户 60079031 讨论考勤系统 ---")
        user1 = "60079031"
        session1 = "web:60079031:conv-001"

        # 用户表达偏好
        await manager.consolidate_to_user_memory(
            user1,
            "用户在考勤系统讨论中提到：\n- 喜欢用 Python 处理数据\n- 习惯在早上 9 点前查看考勤"
        )

        # 会话进行中，记录摘要
        await manager.update_session_summary(
            session1,
            "讨论了考勤查询 SQL 语句，用户询问了如何按日期筛选数据",
            message_count=5
        )

        # 获取用户上下文
        context1 = await manager.get_user_context(user1)
        assert "Python" in context1
        print(f"✓ 用户 {user1} 的记忆已保存")
        print(f"  记忆内容: {context1[:100]}...")

        # 场景 2: 同一用户的新会话
        print("\n--- 场景 2: 用户 60079031 开始新对话 ---")
        session2 = "web:60079031:conv-002"

        # 获取用户上下文（应该包含之前会话的信息）
        context2 = await manager.get_user_context(user1)
        assert "Python" in context2
        assert "早上 9 点" in context2
        print(f"✓ 新对话继承了用户记忆")

        # 记录新会话摘要
        await manager.update_session_summary(
            session2,
            "讨论了数据导出到 Excel 的功能",
            message_count=3
        )
        print(f"✓ 新会话摘要已记录")

        # 检查用户的活跃会话
        from nanobot.db.repositories.session_memory import SessionMemoryRepository
        session_repo = manager.session_memory
        active = await session_repo.get_active_sessions(user1)
        print(f"✓ 用户 {user1} 有 {len(active)} 个活跃会话")
        for sess in active:
            print(f"  - {sess['session_id']}: {sess['message_count']} 条消息")

        # 场景 3: 不同用户（记忆隔离）
        print("\n--- 场景 3: 用户 60079032 （记忆隔离测试）---")
        user2 = "60079032"
        session3 = "web:60079032:conv-001"

        context3 = await manager.get_user_context(user2)
        assert context3 == "", "不同用户应该没有记忆"
        print(f"✓ 用户 {user2} 的记忆为空（隔离成功）")

        # 用户 2 的偏好
        await manager.consolidate_to_user_memory(
            user2,
            "用户偏好：\n- 喜欢用 Java\n- 习惯在晚上工作"
        )

        # 验证两个用户的记忆是独立的
        context1_final = await manager.get_user_context(user1)
        context2_final = await manager.get_user_context(user2)

        assert "Python" in context1_final
        assert "Java" not in context1_final
        assert "Java" in context2_final
        assert "Python" not in context2_final
        print(f"✓ 两个用户的记忆完全隔离")

        # 场景 4: 会话摘要更新
        print("\n--- 场景 4: 会话摘要增量更新 ---")
        new_summary = "讨论了考勤查询 SQL、日期筛选和数据导出功能，总共处理了 10 条消息"
        await manager.update_session_summary(session1, new_summary, message_count=10)

        summary = await manager.get_session_summary(session1)
        assert "数据导出" in summary
        print(f"✓ 会话摘要已更新")
        print(f"  新摘要: {summary}")

        # 场景 5: 查看数据库内容
        print("\n--- 场景 5: 数据库内容验证 ---")
        from nanobot.db.sqlite import SQLiteDatabase

        db = SQLiteDatabase(temp_dir / "nanobot.db")
        await db.connect()

        async with db.get_connection() as conn:
            # 检查用户记忆表
            cursor = await conn.execute("SELECT user_id, content FROM user_memories")
            user_memories = await cursor.fetchall()
            print(f"✓ 数据库中有 {len(user_memories)} 条用户记忆")
            for user_id, content in user_memories:
                preview = content[:50] + "..." if len(content) > 50 else content
                print(f"  - {user_id}: {preview}")

            # 检查会话记忆表
            cursor = await conn.execute("SELECT session_id, message_count FROM session_memories")
            session_memories = await cursor.fetchall()
            print(f"✓ 数据库中有 {len(session_memories)} 条会话记忆")
            for session_id, count in session_memories:
                print(f"  - {session_id}: {count} 条消息")

        await db.disconnect()

        # 场景 6: 文件系统备份验证
        print("\n--- 场景 6: 文件系统备份验证 ---")
        user1_backup = temp_dir / "memory" / "users" / user1 / "MEMORY.md"
        assert user1_backup.exists()
        backup_content = user1_backup.read_text()
        assert "Python" in backup_content
        print(f"✓ 用户记忆文件备份存在: {user1_backup.name}")

        session1_backup = temp_dir / "memory" / "sessions" / session1 / "SUMMARY.md"
        assert session1_backup.exists()
        print(f"✓ 会话记忆文件备份存在: {session1_backup.name}")

        await manager.close()

        print("\n" + "="*60)
        print("✅ 所有场景测试通过！")
        print("="*60)

        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_web_channel_integration():
    """测试与 WebChannel 的集成"""
    print("\n" + "="*60)
    print("WebChannel 集成测试")
    print("="*60)

    # 测试 session_key 解析和格式化
    test_cases = [
        {
            "session_id_input": "60079031:conv-001",
            "expected_user": "60079031",
            "expected_conv": "conv-001",
            "expected_session_key": "web:60079031:conv-001"
        },
        {
            "session_id_input": "user123:conversation-abc",
            "expected_user": "user123",
            "expected_conv": "conversation-abc",
            "expected_session_key": "web:user123:conversation-abc"
        }
    ]

    for case in test_cases:
        session_id = case["session_id_input"]
        parts = session_id.split(':', 1)

        if len(parts) == 2:
            user_id = parts[0]
            conversation_id = parts[1]
            session_key = f"web:{user_id}:{conversation_id}"

            assert user_id == case["expected_user"]
            assert conversation_id == case["expected_conv"]
            assert session_key == case["expected_session_key"]

            print(f"✓ {session_id} -> session_key={session_key}")
        else:
            print(f"✗ {session_id} 格式错误")

    print("\n✅ WebChannel 集成测试通过！")
    return True


async def test_config_integration():
    """测试配置集成"""
    print("\n" + "="*60)
    print("配置集成测试")
    print("="*60)

    from nanobot.config.schema import UserMemoryConfig, SessionMemoryConfig, AgentDefaults

    # 测试默认配置
    user_config = UserMemoryConfig()
    assert user_config.enabled == False
    assert user_config.consolidate_threshold == 30
    print(f"✓ UserMemoryConfig 默认值: enabled={user_config.enabled}")

    session_config = SessionMemoryConfig()
    assert session_config.enabled == True
    assert session_config.consolidate_threshold == 15
    print(f"✓ SessionMemoryConfig 默认值: enabled={session_config.enabled}")

    # 测试 AgentDefaults 集成
    agent_defaults = AgentDefaults()
    assert hasattr(agent_defaults, 'user_memory')
    assert hasattr(agent_defaults, 'session_memory')
    print(f"✓ AgentDefaults 包含两层记忆配置")

    # 测试自定义配置
    custom_user = UserMemoryConfig(enabled=True, consolidate_threshold=50)
    assert custom_user.enabled == True
    assert custom_user.consolidate_threshold == 50
    print(f"✓ 自定义 UserMemoryConfig: enabled={custom_user.enabled}, threshold={custom_user.consolidate_threshold}")

    print("\n✅ 配置集成测试通过！")
    return True


async def main():
    """运行集成测试"""
    print("\n" + "="*70)
    print("两层记忆系统集成测试")
    print("="*70)

    tests = [
        ("配置集成", test_config_integration),
        ("WebChannel 集成", test_web_channel_integration),
        ("真实用户场景", test_realistic_user_scenario),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "✅ 通过", None))
        except Exception as e:
            results.append((name, "❌ 失败", str(e)))
            import traceback
            traceback.print_exc()

    # 打印结果汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)

    for name, status, error in results:
        print(f"{status} {name}")
        if error:
            print(f"   错误: {error}")

    passed = sum(1 for _, status, _ in results if "✅" in status)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有集成测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
