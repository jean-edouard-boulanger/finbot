from typing import Optional, List
import zmq


class SchedClient(object):
    def __init__(self, server_endpoint: str):
        self._socket = zmq.Context().socket(zmq.PUSH)
        self._socket.connect(server_endpoint)
        self._socket.set(zmq.LINGER, 1000)

    def trigger_valuation(self, user_account_id: int, linked_accounts: Optional[List[int]] = None):
        request = {
            "user_account_id": user_account_id,
            "linked_accounts": linked_accounts
        }
        import logging
        logging.info(request)
        self._socket.send_json(request, zmq.DONTWAIT)

    def close(self):
        self._socket.close()
