from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class HexRequestType(Enum):
    PING = ord(b'1')
    APP_VERSION = ord(b'3')
    PRODUCT_ID = ord(b'4')
    RESTART = ord(b'6')
    GET = ord(b'7')
    SET = ord(b'8')
    ASYNC = ord(b'A')


@dataclass(frozen=True, order=True) # type: ignore -- for some reason mypy doesn't like this, even though it is perfectly valid.
class HexDataRequest(ABC):
    payload: Optional[bytes]

    @abstractmethod
    @staticmethod
    def type() -> HexRequestType:
        ...

    def serialize(self) -> bytes:
        payload_len = len(self.payload) if self.payload is not None else 0
        buf = bytearray(2 + payload_len * 2)
        buf[0] = ord(b':')
        buf[1] = self.type().value
        if self.payload is not None and payload_len > 0:
            buf[2:] = self.payload.hex().encode('ascii').upper()
        return bytes(buf)

    @staticmethod
    def ping_request():
        return PingRequest(None)

    @staticmethod
    def app_version_request():
        return AppVersionRequest(None)

    @staticmethod
    def product_id_request():
        return ProductIdRequest(None)

    @staticmethod
    def restart_request():
        return RestartRequest(None)

    @staticmethod
    def get_request(value_id: int):
        return GetRequest(value_id.to_bytes(2, 'little')+ b'\x00' )

    @staticmethod
    def set_request(value_id: int, value: bytes):
        buf = bytearray(2 + 1 + len(value))
        buf[0:2] = value_id.to_bytes(2, 'little')
        buf[3:] = value
        return SetRequest(bytes(buf))

    @staticmethod
    def async_request(value_id: int, value: bytes):
        buf = bytearray(2 + 1 + len(value))
        buf[0:2] = value_id.to_bytes(2, 'little')
        buf[3:] = value
        return SetRequest(bytes(buf))

class PingRequest(HexDataRequest):
    payload: None

    @staticmethod
    def type():
        return HexRequestType.PING

class AppVersionRequest(HexDataRequest):
    payload: None
    
    @staticmethod
    def type():
        return HexRequestType.APP_VERSION

class ProductIdRequest(HexDataRequest):
    payload: None

    @staticmethod
    def type():
        return HexRequestType.PRODUCT_ID

class RestartRequest(HexDataRequest):
    payload: None

    @staticmethod
    def type():
        return HexRequestType.RESTART

class GetRequest(HexDataRequest):
    payload: bytes

    @property
    def value_id(self) -> int:
        return int.from_bytes(memoryview(self.payload)[:2], 'little')
    
    @staticmethod
    def type():
        return HexRequestType.GET

class SetRequest(HexDataRequest):
    payload: bytes

    @property
    def value_id(self) -> int:
        return int.from_bytes(memoryview(self.payload)[:2], 'little')

    @property
    def value(self) -> bytes:
        return self.payload[3:]

    @staticmethod
    def type():
        return HexRequestType.SET

class AsyncRequest(HexDataRequest):
    payload: bytes

    @property
    def value_id(self) -> int:
        return int.from_bytes(memoryview(self.payload)[:2], 'little')
    @property
    def value(self) -> bytes:
        return self.payload[3:]

    @staticmethod
    def type():
        return HexRequestType.ASYNC
