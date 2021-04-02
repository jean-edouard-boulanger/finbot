from marshmallow_dataclass import dataclass
from typing import Optional, List, Union, Type, Dict
import marshmallow_dataclass
import zmq


@dataclass
class TriggerValuationRequest:
    user_account_id: int
    linked_accounts: Optional[List[int]] = None


@dataclass
class Request:
    trigger_valuation: Optional[TriggerValuationRequest] = None


def serialize(obj: Union[Request, TriggerValuationRequest]) -> Dict:
    schema = marshmallow_dataclass.class_schema(type(obj))()
    return schema.dump(obj)


def deserialize(obj_type: Type, data: Dict):
    schema = marshmallow_dataclass.class_schema(obj_type)()
    return schema.load(data)


class SchedClient(object):
    def __init__(self, server_endpoint: str):
        self._socket = zmq.Context().socket(zmq.PUSH)
        self._socket.connect(server_endpoint)
        self._socket.set(zmq.LINGER, 1000)

    def trigger_valuation(self, request: TriggerValuationRequest):
        self._socket.send_json(
            serialize(Request(trigger_valuation=request)), zmq.DONTWAIT
        )

    def close(self):
        self._socket.close()
