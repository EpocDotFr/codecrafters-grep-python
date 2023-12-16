from typing import List, Union
import dataclasses
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


@dataclasses.dataclass
class Literal:
    value: bytes
    count: Count


@dataclasses.dataclass
class Digit:
    count: Count


@dataclasses.dataclass
class Alphanumeric:
    count: Count


@dataclasses.dataclass
class CharacterSet:
    mode: CharacterSetMode
    values: bytes
    count: Count


@dataclasses.dataclass
class Wildcard:
    count: Count


@dataclasses.dataclass
class AlternationGroup:
    choices: List[List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard]]] # AlternationGroup and Group as well


@dataclasses.dataclass
class Group:
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup]] # Group as well


@dataclasses.dataclass
class Pattern:
    start: bool = False
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, Group, AlternationGroup]] = dataclasses.field(default_factory=list)
    end: bool = False
