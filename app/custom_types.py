from collections import namedtuple
from enum import Enum


class Count(Enum):
    One = None
    OneOrMore = '+'
    ZeroOrOne = '?'


class CharacterSetMode(Enum):
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

CharacterSet = namedtuple('CharacterSet', [
    'mode',
    'values'
])

Wildcard = namedtuple('Wildcard', [
    'count'
])

AlternationGroup = namedtuple('AlternationGroup', [
    'choices'
])

GroupBackreference = namedtuple('GroupBackreference', [
    'reference'
])
