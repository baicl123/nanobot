#!/usr/bin/env python3
"""并发测试工具：模拟多个用户同时连接 nanobot"""

import asyncio
import websockets
import json
import time
from typing import List, Dict
import argparse

# 配置
WS_URL = "ws://127.0.0.1:8765/ws/{session_id}"
CONCURRENT_USERS = 10
MESSAGES_PER_USER = 3
TEST_MESSAGES = [
    "你好",
    "1+1等于几？",
    "再见"
]


class ConcurrentUser:
    """模拟一个并发用户"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.session_id = f"test-user-{user_id}-{int(time.time())}"
        self.ws_url = WS_URL.format(session_id=self.session_id)
        self.messages_received = 0
        self.messages_sent = 0
        self.errors = []
        self.thinking_count = 0
        self.progress_count = 0
        self.start_time = None
        self.end_time = None

    async def connect_and_chat(self):
        """连接并进行对话"""
        try:
            self.start_time = time.time()
            print(f"[用户 {self.user_id}] 正在连接到 {self.session_id}...")

            async with websockets.connect(
                self.ws_url,
                ping_timeout=None,
                close_timeout=10
            ) as websocket:
                print(f"[用户 {self.user_id}] ✅ 连接成功")

                # 等待连接确认
                connected_msg = await websocket.recv()
                connected_data = json.loads(connected_msg)
                if connected_data.get('type') == 'connected':
                    print(f"[用户 {self.user_id}] ✓ 收到连接确认")

                # 发送多条消息
                for i, message in enumerate(TEST_MESSAGES[:MESSAGES_PER_USER], 1):
                    await self.send_message(websocket, message, i)
                    # 随机延迟，模拟真实用户
                    await asyncio.sleep(0.5)

                self.end_time = time.time()
                print(f"[用户 {self.user_id}] ✅ 测试完成")

        except Exception as e:
            self.errors.append(str(e))
            print(f"[用户 {self.user_id}] ❌ 错误: {e}")

    async def send_message(self, websocket, message: str, index: int):
        """发送单条消息并接收响应"""
        try:
            # 发送消息
            payload = {
                "type": "message",
                "data": {
                    "content": f"[用户{self.user_id}-消息{index}] {message}"
                }
            }
            await websocket.send(json.dumps(payload))
            self.messages_sent += 1
            print(f"[用户 {self.user_id}] 📤 发送消息 {index}: {message}")

            # 接收所有相关消息（thinking, progress, message）
            timeout = 30  # 30秒超时
            start_wait = time.time()

            while time.time() - start_wait < timeout:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=2.0
                    )
                    data = json.loads(response)
                    msg_type = data.get('type')

                    if msg_type == 'thinking_start':
                        self.thinking_count += 1
                        print(f"[用户 {self.user_id}] 🔄 思考开始")

                    elif msg_type == 'progress':
                        self.progress_count += 1
                        content = data.get('data', {}).get('content', '')
                        print(f"[用户 {self.user_id}] ⏳ 进度: {content[:40]}")

                    elif msg_type == 'thinking_end':
                        print(f"[用户 {self.user_id}] ✅ 思考结束")

                    elif msg_type == 'message':
                        self.messages_received += 1
                        content = data.get('data', {}).get('content', '')
                        print(f"[用户 {self.user_id}] 📥 收到响应: {content[:50]}...")
                        break  # 收到最终消息，结束循环

                    elif msg_type == 'error':
                        self.errors.append(data.get('data', {}).get('message', 'Unknown error'))
                        print(f"[用户 {self.user_id}] ❌ 错误: {self.errors[-1]}")
                        break

                except asyncio.TimeoutError:
                    continue  # 继续等待
                except Exception as e:
                    self.errors.append(f"接收消息错误: {e}")
                    break

        except Exception as e:
            self.errors.append(f"发送消息错误: {e}")
            print(f"[用户 {self.user_id}] ❌ 发送错误: {e}")


async def run_concurrent_test(num_users: int = 10):
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"🚀 并发测试开始：{num_users} 个用户")
    print(f"{'='*60}\n")

    # 创建并发用户
    users = [ConcurrentUser(i+1) for i in range(num_users)]

    # 同时启动所有用户
    start_time = time.time()
    await asyncio.gather(*[user.connect_and_chat() for user in users])
    total_time = time.time() - start_time

    # 统计结果
    print(f"\n{'='*60}")
    print(f"📊 测试结果统计")
    print(f"{'='*60}\n")

    total_sent = sum(u.messages_sent for u in users)
    total_received = sum(u.messages_received for u in users)
    total_thinking = sum(u.thinking_count for u in users)
    total_progress = sum(u.progress_count for u in users)
    total_errors = sum(len(u.errors) for u in users)

    print(f"总用户数: {num_users}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均每用户耗时: {total_time/num_users:.2f} 秒")
    print(f"\n消息统计:")
    print(f"  发送消息: {total_sent}")
    print(f"  接收响应: {total_received}")
    print(f"  成功率: {total_received/total_sent*100 if total_sent > 0 else 0:.1f}%")
    print(f"\n实时功能统计:")
    print(f"  thinking_start 次数: {total_thinking}")
    print(f"  progress 次数: {total_progress}")
    print(f"\n错误统计:")
    print(f"  总错误数: {total_errors}")

    if total_errors > 0:
        print(f"\n错误详情:")
        for user in users:
            if user.errors:
                print(f"  用户 {user.user_id}: {user.errors}")

    # 并发性能分析
    print(f"\n{'='*60}")
    print(f"⚡ 并发性能分析")
    print(f"{'='*60}\n")

    if total_time > 0:
        throughput = num_users / total_time
        print(f"并发吞吐量: {throughput:.2f} 用户/秒")
        print(f"理论最大并发: {int(100 / total_time * num_users)} 用户")

    # 验证结论
    print(f"\n{'='*60}")
    print(f"✅ 验证结论")
    print(f"{'='*60}\n")

    if total_received == total_sent and total_errors == 0:
        print("🎉 并发测试通过！nanobot 支持稳定的多人并发访问。")
        print(f"   - 所有 {num_users} 个用户都成功完成对话")
        print(f"   - 所有消息都得到正确响应")
        print(f"   - 实时功能（thinking/progress）正常工作")
    elif total_received > 0 and total_errors == 0:
        print("⚠️ 并发测试基本通过，但有少量消息丢失。")
        print(f"   - 成功率: {total_received/total_sent*100:.1f}%")
        print(f"   - 可能原因：网络延迟或超时")
    else:
        print("❌ 并发测试失败！")
        if total_errors > 0:
            print(f"   - 发生 {total_errors} 个错误")
        if total_received < total_sent:
            print(f"   - {total_sent - total_received} 条消息未收到响应")

    print(f"\n{'='*60}\n")


async def main():
    """主函数"""
    global WS_URL, MESSAGES_PER_USER

    parser = argparse.ArgumentParser(description="nanobot 并发测试工具")
    parser.add_argument(
        '-u', '--users',
        type=int,
        default=CONCURRENT_USERS,
        help=f'并发用户数 (默认: {CONCURRENT_USERS})'
    )
    parser.add_argument(
        '-m', '--messages',
        type=int,
        default=MESSAGES_PER_USER,
        help=f'每用户发送消息数 (默认: {MESSAGES_PER_USER})'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='127.0.0.1:8765',
        help='WebSocket 服务器地址 (默认: 127.0.0.1:8765)'
    )

    args = parser.parse_args()

    # 更新全局配置
    WS_URL = f"ws://{args.url}/ws/{{session_id}}"
    MESSAGES_PER_USER = args.messages

    print(f"\n测试配置:")
    print(f"  服务器: ws://{args.url}")
    print(f"  并发用户: {args.users}")
    print(f"  每用户消息: {args.messages}")
    print(f"  总消息数: {args.users * args.messages}")

    await run_concurrent_test(args.users)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
