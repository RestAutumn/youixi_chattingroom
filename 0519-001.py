import asyncio
import tkinter as tk
from tkinter import messagebox

import websocket
import websockets
import json
import base64
import os
import datetime
from tkinter import messagebox



# 全局连接列表
connections = []

# 存储聊天记录的列表
chat_history = []

# 存储连接的客户端信息的字典
clients = {}

# 存储被屏蔽的用户的字典
blocked_users = {}

# 存储未读消息数的字典
unread_messages = {}

# 定义全局变量
message_notification = False  # 消息提醒标志

# 定义全局变量
connected_users = {}  # 存储已连接的用户信息

private_chats = {}  # 存储私聊会话信息


# 保存聊天记录到文件
def save_chat_history():
    with open("chat_history.txt", "w") as file:
        for message in chat_history:
            file.write(json.dumps(message) + "\n")

# 加载聊天记录
def load_chat_history():
    if os.path.exists("chat_history.txt"):
        with open("chat_history.txt", "r") as file:
            for line in file:
                message = json.loads(line.strip())
                chat_history.append(message)


# 生成消息ID
def generate_message_id():
    return str(datetime.datetime.now().timestamp())

# 接收系统发送的消息
async def receive_system_message():
    while True:
        # 在这里编写接收系统消息的逻辑，包括调用 WebSocket 接收消息，处理消息等操作
        # 如果收到系统消息，可以通过调用 show_notification() 函数触发消息提醒
        # 注意：由于是在异步循环中运行，可能需要使用 asyncio.sleep() 来控制接收消息的频率
        await asyncio.sleep(1)  # 以1秒的频率进行示例

''''# 创建异步事件循环并启动
async def main():
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(receive_system_message()), loop.create_task(start_server())]
    await asyncio.wait(tasks)

# 运行示例
asyncio.run(main())'''
# 创建异步事件循环并启动
async def main():
    async with websockets.serve(handle_connection, 'localhost', 8000):
        await receive_system_message()


# 获取客户端信息
async def get_client_info(client_websocket):
    # 在这里编写获取客户端信息的逻辑
    # 例如根据客户端的请求参数获取用户名、IP地址等信息
    # 示例：从WebSocket对象的请求中获取远程地址
    client_address = client_websocket.remote_address
    return client_address

# 添加客户端到连接列表
def add_client_to_list(client_websocket, client_info):
    # 在这里编写将客户端添加到连接列表的逻辑
    # 例如将客户端信息保存到一个全局连接列表中
    # 示例：将客户端WebSocket对象和客户端信息作为键值对添加到字典中
    connections[client_websocket] = client_info


async def handle_new_connection(client_websocket, client_address):
    try:
        # 执行与新连接相关的初始化操作
        # 例如发送欢迎消息、获取客户端信息等

        # 示例：发送欢迎消息
        welcome_message = "Welcome to the chat room!"
        await client_websocket.send(welcome_message)

        # 示例：获取客户端信息
        client_info = await get_client_info(client_websocket)

        # 在这里可以根据需求进行其他操作
        # 例如将客户端信息添加到连接列表中

        # 添加到连接列表
        add_client_to_list(client_websocket, client_info)

        # 打印连接信息
        print(f"New connection from {client_address}")

    except Exception as e:
        # 处理连接初始化过程中的异常
        print(f"Error handling new connection from {client_address}: {str(e)}")
        await client_websocket.close()

# 处理WebSocket连接，最基本的那个函数
async def handle_connection(websocket, path):
    # 接收客户端的连接请求
    client_id = await websocket.recv()
    #不知道这里要不要填个数字来限制消息大小
    print(f"New client connected: {client_id}")

    # 添加客户端到字典中
    clients[client_id] = websocket

    # 发送欢迎消息给客户端
    welcome_message = {
        "id": generate_message_id(),
        "type": "system",
        "content": "Welcome to the chat room!"
    }
    await websocket.send(json.dumps(welcome_message))

    # 处理客户端发送的消息
    try:
        async for message in websocket:
            await handle_message(message, client_id)
    except websockets.exceptions.ConnectionClosedOK:
        # 连接关闭
        pass
    finally:
        # 从字典中删除客户端
        del clients[client_id]
        print(f"Client disconnected: {client_id}")

# 处理收到的消息
async def handle_message(message, client_id):
    # 解析收到的消息
    try:
        data = json.loads(message)
        msg_type = data["type"]
        content = data["content"]
    except (json.JSONDecodeError, KeyError):
        # 消息解析错误，忽略该消息
        return

    if msg_type == "text":
        # 处理文本消息
        sender = client_id
        timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 创建文本消息
        text_message = {
            "id": message_id,
            "type": "text",
            "sender": sender,
            "timestamp": timestamp,
            "content": content
        }

        # 保存到聊天记录
        chat_history.append(text_message)
        save_chat_history()

        # 转发消息给其他客户端
        for client in clients.values():
            if client != websocket:
                await client.send(json.dumps(text_message))

    elif msg_type == "image":
        # 处理图片消息
        sender = client_id
        timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 解码图片数据
        image_data = base64.b64decode(content)

        # 生成图片文件名
        image_filename = f"image_{message_id}.png"

        # 保存图片文件
        with open(image_filename, "wb") as file:
            file.write(image_data)

        # 创建图片消息
        image_message = {
            "id": message_id,
            "type": "image",
            "sender": sender,
            "timestamp": timestamp,
            "content": image_filename
        }

        # 保存到聊天记录
        chat_history.append(image_message)
        save_chat_history()

        # 转发消息给其他客户端
        for client in clients.values():
            if client != websocket:
                await client.send(json.dumps(image_message))

    elif msg_type == "system":
        # 处理系统发送的消息
        system_message = content

        if system_message == "block_user":
            # 屏蔽用户
            blocked_user = client_id
            blocked_users[blocked_user] = True

            # 发送确认消息给客户端
            response = {
                "id": generate_message_id(),
                "type": "system",
                "content": f"You have blocked user: {blocked_user}"
            }
            await websocket.send(json.dumps(response))

        elif system_message == "unblock_user":
            # 解除屏蔽用户
            blocked_user = client_id
            if blocked_user in blocked_users:
                del blocked_users[blocked_user]

            # 发送确认消息给客户端
            response = {
                "id": generate_message_id(),
                "type": "system",
                "content": f"You have unblocked user: {blocked_user}"
            }
            await websocket.send(json.dumps(response))
    elif msg_type == "private":
        # 处理私聊消息
        sender = client_id
        recipient = content.get("recipient", "")
        message_content = content.get("content", "")

        if recipient and message_content:
            handle_private_message(sender, recipient, message_content)

# 创建私聊消息
def create_private_message(message_id, sender, recipient, content):
    timestamp = datetime.datetime.now().timestamp()

    private_message = {
        "id": message_id,
        "type": "private",
        "sender": sender,
        "recipient": recipient,
        "timestamp": timestamp,
        "content": content
    }

    return private_message

# 处理私聊消息
def handle_private_message(sender, recipient, content):
    # 创建私聊消息
    message_id = generate_message_id()
    private_message = create_private_message(message_id, sender, recipient, content)

    # 保存到聊天记录
    chat_history.append(private_message)
    save_chat_history()

    # 转发消息给发送者和接收者
    send_private_message(sender, recipient, private_message)

# 发送私聊消息
def send_private_message(sender, recipient, message):
    # 检查接收者是否在线
    if recipient in connected_users:
        recipient_websocket = connected_users[recipient]

        # 发送私聊消息给接收者
        recipient_websocket.send(json.dumps(message))

    # 发送私聊消息给发送者
    sender_websocket = connected_users[sender]
    sender_websocket.send(json.dumps(message))

    # 定义发送消息的函数
def send_message():
    # 发送消息给指定客户端
    def send_message(recipient, message):
        if recipient in clients:
            client_websocket = clients[recipient]
            client_websocket.send(json.dumps(message))
        else:
            print(f"Error: Client {recipient} not found.")

async def handle_connection_closed(client_websocket):
    # 在这里编写处理连接关闭的逻辑
    # 您可以根据需要执行一些清理操作或通知其他用户等

    # 例如，输出一条连接关闭的消息
    print("连接已关闭")

    # 或者，向其他用户广播连接关闭的消息
    # 使用 WebSocket 连接对象的 `.send()` 方法发送消息
    # 广播消息的具体实现可能因您的应用需求而异

    # 关闭 WebSocket 连接
    await client_websocket.close()


# 运行示例
async def start_server():
    # 启动
    async with websockets.serve(handle_connection, "localhost", 8000):
        # 创建WebSocket服务器
        server = await websockets.serve(handle_connection, "localhost", 8000)
        print("WebSocket server started.")
        # 进入事件循环，处理连接和消息
        while True:
            # 接收连接请求
            #client_websocket, client_address = await asyncio.get_event_loop().sock_accept(server)
            # 接收连接请求
            client_websocket, client_address = await server.accept()

            # 处理新连接
            await handle_new_connection(client_websocket, client_address)

            # 接收和处理消息
            try:
                async for message in client_websocket:
                    await handle_message(client_websocket, message)
            except websockets.exceptions.ConnectionClosed:
                # 连接关闭时的处理
                await handle_connection_closed(client_websocket)
# 启动聊天室
if __name__ == "__main__":
    load_chat_history()  # 加载聊天记录
    asyncio.run(main())  # 启动异步事件循环
    #asyncio.run(main())





