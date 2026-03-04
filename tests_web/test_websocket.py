#!/usr/bin/env python3
"""快速测试 WebSocket 连接"""

import asyncio
import websockets
import json

async def test_websocket_connection():
    """测试 WebSocket 连接是否能正常建立和保持"""
    print("测试 WebSocket 连接...")

    # 测试连接
    session_id = "test_user:conv-test-001"
    user_id = "test_user"
    uri = f"ws://localhost:8765/ws/{session_id}?user_id={user_id}"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ 连接成功: {uri}")

            # 等待连接确认消息
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"✓ 收到消息: type={data.get('type')}")

            if data.get('type') == 'connected':
                print(f"✓ 连接确认成功")
                print(f"  - session_id: {data['data'].get('session_id')}")
                print(f"  - conversation_id: {data['data'].get('conversation_id')}")
                print(f"  - user_id: {data['data'].get('user_id')}")
                print(f"  - session_key: {data['data'].get('session_key')}")
            else:
                print(f"✗ 未收到 connected 消息")
                return False

            # 发送 ping 测试
            ping_msg = {
                "type": "ping",
                "data": {}
            }
            await websocket.send(json.dumps(ping_msg))
            print(f"✓ 发送 ping")

            # 等待 pong
            pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            pong_data = json.loads(pong_response)
            if pong_data.get('type') == 'pong':
                print(f"✓ 收到 pong 响应")
            else:
                print(f"? 收到其他响应: {pong_data.get('type')}")

            print(f"\n✅ WebSocket 连接测试通过！")
            return True

    except asyncio.TimeoutError:
        print(f"✗ 连接超时")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        print(f"✗ 连接被关闭: code={e.code}, reason={e.reason}")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_connections():
    """测试多个连接"""
    print("\n" + "="*60)
    print("测试多个 WebSocket 连接...")
    print("="*60)

    tasks = []
    for i in range(3):
        session_id = f"user{i}:conv-{i}"
        user_id = f"user{i}"
        uri = f"ws://localhost:8765/ws/{session_id}?user_id={user_id}"
        tasks.append(test_single_connection(uri, i))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = sum(1 for r in results if r is True)

    print(f"\n✓ {success}/3 连接成功")

    return success == 3


async def test_single_connection(uri, index):
    """测试单个连接"""
    try:
        async with websockets.connect(uri) as websocket:
            await asyncio.sleep(0.5)  # 等待连接建立
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            data = json.loads(response)
            if data.get('type') == 'connected':
                print(f"✓ 连接 {index} 成功: {data['data'].get('session_key')}")
                return True
        return False
    except Exception as e:
        print(f"✗ 连接 {index} 失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("WebSocket 连接测试")
    print("="*60)
    print("\n确保 nanobot gateway 正在运行: nanobot gateway")
    print()

    # 等待用户确认
    import sys
    if "--no-wait" not in sys.argv:
        input("按 Enter 开始测试...")

    # 测试单个连接
    success1 = await test_websocket_connection()

    # 测试多个连接
    success2 = await test_multiple_connections()

    if success1 and success2:
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  部分测试失败")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
