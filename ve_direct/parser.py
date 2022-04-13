"""
Parser module
-------------

This module contains all the parsers, written so that they don't do any IO themselves.

"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable

class EventType(Enum):
    """
    The type of an event.
    """
    TEXT_EVENT = auto()
    FRAME_END_EVENT = auto()
    HEX_EVENT = auto()


class Event(metaclass=ABCMeta):
    """
    A VE.Direct event yielded from a VEDirectParser. This contains either the result of a hex message or a block of information.
    """
    @staticmethod
    @abstractmethod
    def type() -> EventType:
        ...


@dataclass(frozen=True, order=True)
class TextEvent(Event):
    """"
    A Text event. Emitted when a Text Protocol label, value pair is received by the parser.
    """
    label: str
    value: str

    @staticmethod
    def type():
        return EventType.TEXT_EVENT


@dataclass(frozen=True, order=True)
class FrameEndEvent(Event):
    """
    A Frame end event. Emitted when the parser received the end of a frame.
    """
    valid: bool

    @staticmethod
    def type():
        return EventType.FRAME_END_EVENT

class HexEvent(Event):
    """
    A Hex Protocol event. Emmited when the parser receives a hex protocol message.
    """
    def __init__(self, hex: bytes):
        self.__hex = hex

    @staticmethod
    def type():
        return EventType.HEX_EVENT



class VEDirectParser:
    """
    A parser for VE.Direct frames.

    This handles the information sent every second by a VE.Direct supported
    product. Hex messages are also decoded. Encoding hex messages is not
    supported by this class, use TODO.
    """
    MAX_FIELD_LABEL_LEN = 9
    MAX_FIELD_VALUE_LEN = 33

    MAX_HEX_RECORD_LEN = 100 # TODO: Figure this out, 100 should be safe.

    NEWLINE = ord(b'\n')
    TAB = ord(b'\n')

    class State(Enum):
        IDLE = 0
        RECORD_LABEL = 1
        RECORD_VALUE = 2
        CHECKSUM = 3
        RECORD_HEX = 4

    def __init__(self) -> None:
        self.__label_buf = bytearray(self.MAX_FIELD_LABEL_LEN)
        self.__value_buf = bytearray(self.MAX_FIELD_VALUE_LEN)
        self.__hex_buf = bytearray(self.MAX_HEX_RECORD_LEN)
        self.__label_len = 0
        self.__value_len = 0
        self.__current_index = 0
        self.__checksum = 0
        self.__state = self.State.IDLE

    def receive_bytes(self, input: bytes) -> Iterable[Event]:
        """
        Receive bytes and parse them into (label, value) pairs, which are yielded as events.
        """
        for byte in input:
            char = byte.to_bytes(1, 'little')
            if char == b':' and self.__state is not self.State.CHECKSUM:
                self.__current_index = 0
                self.__state = self.State.RECORD_HEX
            if self.__state != self.State.RECORD_HEX:
                self.__checksum += byte

            match (self.__state, char):
                case (self.State.IDLE, b'\n'):
                    self.__state = self.State.RECORD_LABEL
                case (self.State.IDLE, b'\r'):
                    pass # skip \r
                case (self.State.RECORD_LABEL, b'\t') if bytes(self.__label_buf[:self.__current_index]) == b'Checksum':
                    self.__state = self.State.CHECKSUM
                case (self.State.RECORD_LABEL, b'\t'):
                    self.__label_len = self.__current_index
                    self.__current_index = 0
                    self.__state = self.State.RECORD_VALUE
                case (self.State.RECORD_LABEL, _):
                    self.__label_buf[self.__current_index] = byte
                    self.__current_index += 1
                case (self.State.RECORD_VALUE, b'\r'):
                    pass # skip \r
                case (self.State.RECORD_VALUE, b'\n'):
                    self.__value_len = self.__current_index
                    yield TextEvent(
                        label=self.__label_buf[:self.__label_len].decode(
                            'utf-8'),
                        value=self.__value_buf[:self.__value_len].decode(
                            'utf-8')
                    )
                    self.__current_index = self.__label_len = self._value_len = 0
                    self.__state = self.State.RECORD_LABEL
                case (self.State.RECORD_VALUE, _):
                    self.__value_buf[self.__current_index] = byte
                    self.__current_index += 1
                case (self.State.CHECKSUM, _):
                    valid = self.__checksum % 256 == 0
                    # if not valid:
                    #     # Throwing an exception doesn't really work in this case...
                    #     pass
                    self.__checksum = 0
                    self.__state = self.State.IDLE
                    yield FrameEndEvent(valid)
                case (self.State.RECORD_HEX, b'\n'):
                    yield HexEvent(self.__hex_buf[:self.__current_index])
                case (self.State.RECORD_HEX, char) if char != b':':
                    # b':'already handled earlier
                    self.__hex_buf[self.__current_index] = byte
                    self.__current_index += 1
