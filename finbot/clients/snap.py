import requests
import json


class Error(RuntimeError):
    pass


class SnapClient(object):
    def __init__(self, server_endpoint):
        self.server_endpoint = server_endpoint

    def take_snapshot(self, account_id):
        response = requests.get(f"{self.server_endpoint}/snapshot/{account_id}")
        if not response:
            raise Error(f"failure while taking snapshot (code {response.status_code})")
        return json.loads(response.content)["snapshot_id"]
