#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'  # можно указать тип до объявления класса в ''
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes) -> None:
        """
        получает все, что пишут пользователи
        """
        print(data)
        decoded = data.decode()

        if self.login is not None:  # если у пользователя уже есть логин, то его сообщения печатаются в общем чате
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login: ", "").replace("\r\n", "")
                # присваеваем временный логин для дальнейшей проверки
                if tmp_login in self.server.logged_users:  # Если этот логин уже занят,
                    # выводим сообщение и отключаем соединение
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой\n".encode())
                    self.connection_lost()
                else:
                    self.login = tmp_login  # присваеваем логин пользователю
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.server.logged_users.add(self.login)  # добавляем новый логин во множество
                    self.send_history(self.server.chat_history)  # выводим историю сообщений чата
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.BaseTransport) -> None:
        """
        вызывается, когда новый пользователь подключается к серверу
        """
        self.server.clients.append(self)  # добавляет пользователя в список
        self.transport = transport  # интерфейс подключения
        print("Пришел новый клиент")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """
        вызывается, когда пользователь отключается от сервера
        """
        self.server.clients.remove(self)  # удаляем пользователя из списка
        print("Клиент вышел")

    def send_message(self, content):
        """
        принимает сообщения пользователей
        """
        message = f"{self.login}: {content}\n"
        if len(self.server.chat_history) < 10:  # накапливает последние 10 сообщений пользователей в список
            self.server.chat_history.append(message)
        else:
            self.server.chat_history.pop(0)  # убирает неактуальное сообщение
            self.server.chat_history.append(message)  # добавляет новое
        for user in self.server.clients:  # отсылает сообщение пользователя всем подключенным пользователям
            user.transport.write(message.encode())

    def send_history(self, content_history):  # функция вывода истории сообщений для новых пользователей
        for message in content_history:
            self.transport.write(message.encode())


class Server:
    """
    принимает запросы пользователей
    """
    clients: list
    logged_users: set
    chat_history: list

    def __init__(self):
        self.clients = []  # список всех вошедших на сервер
        self.logged_users = set()  # хранит логины зарегестрированных пользователей
        self.chat_history = []  # лист для накопления истории чата

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            "192.168.0.27",
            8888
        )

        print("Сервер запущен...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
