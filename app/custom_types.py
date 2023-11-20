from collections import namedtuple
from enum import Enum


class Count(Enum):
    One = None
    OneOrMore = '+'
    ZeroOrOne = '?'


class CharacterGroupMode(Enum):
    Positive = None
    Negative = '^'

Pattern = namedtuple('Pattern', [
    'start',
    'items',
    'end'
])

Literal = namedtuple('Literal', [
    'value',
    'count'
])

Digit = namedtuple('Digit', [
    'count'
])

Alphanumeric = namedtuple('Alphanumeric', [
    'count'
])

CharacterGroup = namedtuple('CharacterGroup', [
    'mode',
    'values'
])

Wildcard = namedtuple('Wildcard', [
    'count'
])

Alternation = namedtuple('Alternation', [
    'choices'
])
