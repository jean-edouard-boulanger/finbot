from finbot.core.web_service import WebServiceClient


class AppwsrvClient(WebServiceClient):
    service_name = "appwsrv"

    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)
