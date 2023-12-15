from dataclasses import dataclass
from typing import List, Union
from enum import Enum


class Count(Enum):
    One = None
    OneOrMore = b'+'
    ZeroOrOne = b'?'


class CharacterSetMode(Enum):
    Positive = None
    Negative = b'^'


@dataclass
class HasCountMixin:
    count: Count


@dataclass
class Literal(HasCountMixin):
    value: bytes


@dataclass
class Digit(HasCountMixin):
    pass


@dataclass
class Alphanumeric(HasCountMixin):
    pass


@dataclass
class CharacterSet:
    mode: CharacterSetMode
    values: bytes


@dataclass
class Wildcard(HasCountMixin):
    pass


@dataclass
class GroupBackreference:
    reference: int

@dataclass
class Group:
    items: List[Union[Literal, Digit, Alphanumeric, GroupBackreference, CharacterSet, Wildcard]]


@dataclass
class AlternationGroup:
    choices: List[bytes]


@dataclass
class Pattern:
    start: bool
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, Group, AlternationGroup, GroupBackreference]]
    end: bool
