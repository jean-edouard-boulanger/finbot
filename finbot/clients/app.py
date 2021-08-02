from finbot.clients.base import Base as ClientBase


class AppClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)
