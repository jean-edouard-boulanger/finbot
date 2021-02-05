import zmq


class SchedClient(object):
    def __init__(self, server_endpoint: str):
        self._socket = zmq.Context().socket(zmq.PUSH)
        self._socket.connect(server_endpoint)

    def trigger_valuation(self, user_account_id: int):
        self._socket.send_json({
            "user_account_id": user_account_id
        })

    def close(self):
        self._socket.close()
