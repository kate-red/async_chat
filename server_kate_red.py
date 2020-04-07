#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'  # можно указать тип до объявления класса
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes) -> None:
        print(data)
        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)

        else:
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login: ", "").replace("\r\n", "")
                if tmp_login in self.server.logged_users:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой\n".encode())
                    self.connection_lost()
                else:
                    self.login = tmp_login
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.server.logged_users.add(self.login)
                    self.send_history(self.server.chat_history)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.BaseTransport) -> None:
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content):
        message = f"{self.login}: {content}\n"
        if 10 > len(self.server.chat_history):
            self.server.chat_history.append(message)
        else:
            self.server.chat_history.pop(0)
            self.server.chat_history.append(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self, content_history):
        for message in content_history:
            self.transport.write(message.encode())



class Server:
    clients: list
    logged_users: set
    chat_history: list

    def __init__(self):
        self.clients = []
        self.logged_users = set()
        self.chat_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            "192.168.0.25",
            8888
        )

        print("Сервер запущен...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
