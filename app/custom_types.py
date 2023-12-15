from dataclasses import dataclass
from typing import List, Union
import enum


@enum.unique
class Count(enum.Enum):
    One = None
    OneOrMore = b'+'
    ZeroOrOne = b'?'


@enum.unique
class CharacterSetMode(enum.Enum):
    Positive = None
    Negative = b'^'


@dataclass
class Literal:
    value: bytes
    count: Count
    matched: bytes = b''


@dataclass
class Digit:
    count: Count
    matched: bytes = b''


@dataclass
class Alphanumeric:
    count: Count
    matched: bytes = b''


@dataclass
class CharacterSet:
    mode: CharacterSetMode
    values: bytes
    matched: bytes = b''


@dataclass
class Wildcard:
    count: Count
    matched: bytes = b''


@dataclass
class GroupBackreference:
    reference: int


@dataclass
class AlternationGroup:
    choices: List[bytes]
    matched: bytes = b''


@dataclass
class Group:
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, GroupBackreference, AlternationGroup]]


@dataclass
class Pattern:
    start: bool
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, GroupBackreference, Group, AlternationGroup]]
    end: bool
