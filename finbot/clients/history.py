import requests
import json


class Error(RuntimeError):
    pass


class HistoryClient(object):
    def __init__(self, server_endpoint):
        self.server_endpoint = server_endpoint

    def write_history(self, snapshot_id):
        response = requests.post(f"{self.server_endpoint}/history/{snapshot_id}/write")
        if not response:
            raise Error(f"failure while writing history (code {response.status_code})")
        return json.loads(response.content)
