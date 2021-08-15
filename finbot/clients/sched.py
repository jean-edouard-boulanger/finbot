from typing import TYPE_CHECKING
from typing import Optional, Union, Type, Any, TypeVar
import marshmallow_dataclass
import zmq


if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from marshmallow_dataclass import dataclass


@dataclass
class TriggerValuationRequest:
    user_account_id: int
    linked_accounts: Optional[list[int]] = None


@dataclass
class Request:
    trigger_valuation: Optional[TriggerValuationRequest] = None


def serialize(obj: Union[Request, TriggerValuationRequest]) -> Any:
    schema = marshmallow_dataclass.class_schema(type(obj))()
    return schema.dump(obj)


T = TypeVar("T")


def deserialize(obj_type: Type[T], data: dict[Any, Any]) -> T:
    schema = marshmallow_dataclass.class_schema(obj_type)()
    obj: T = schema.load(data)
    return obj


class SchedClient(object):
    def __init__(self, server_endpoint: str):
        self._socket = zmq.Context().socket(zmq.PUSH)  # type: ignore
        self._socket.connect(server_endpoint)
        self._socket.set(zmq.LINGER, 1000)

    def trigger_valuation(self, request: TriggerValuationRequest) -> None:
        self._socket.send_json(
            serialize(Request(trigger_valuation=request)), zmq.DONTWAIT
        )

    def close(self) -> None:
        self._socket.close()
