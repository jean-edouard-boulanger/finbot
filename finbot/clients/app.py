from finbot.clients import Base


class AppClient(Base):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def is_healthy(self) -> bool:
        return self.get("healthy")["healthy"]
