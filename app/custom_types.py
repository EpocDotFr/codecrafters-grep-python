from typing import List, Union, Optional
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
    matched: bytes = b''


@dataclasses.dataclass
class Digit:
    count: Count
    matched: bytes = b''


@dataclasses.dataclass
class Alphanumeric:
    count: Count
    matched: bytes = b''


@dataclasses.dataclass
class CharacterSet:
    mode: CharacterSetMode
    values: bytes
    count: Count
    matched: bytes = b''


@dataclasses.dataclass
class Wildcard:
    count: Count
    matched: bytes = b''


@dataclasses.dataclass
class GroupBackreference:
    reference: int


@dataclasses.dataclass
class AlternationGroup:
    choices: List[List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, GroupBackreference]]] # AlternationGroup and Group as well
    matched_choice: Optional[int] = None

    @property
    def matched(self) -> bytes:
        return b''.join([
            item.matched for item in self.choices[self.matched_choice]
        ])


@dataclasses.dataclass
class Group:
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, GroupBackreference, AlternationGroup]] # Group as well

    @property
    def matched(self) -> bytes:
        return b''.join([
            item.matched for item in self.items
        ])


@dataclasses.dataclass
class Pattern:
    start: bool = False
    items: List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, GroupBackreference, Group, AlternationGroup]] = dataclasses.field(default_factory=list)
    end: bool = False
    groups: List[Union[Group, AlternationGroup]] = dataclasses.field(default_factory=list)
