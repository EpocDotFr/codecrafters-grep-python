from app.custom_types import Count, CharacterSetMode, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Pattern
from typing import Tuple, Union, Callable
from app.lexer import Lexer
from io import BytesIO
import string

METACLASS_DIGITS = string.digits
METACLASS_UPPER_LOWER_LETTERS = string.ascii_letters
METACLASS_DIGITS_UPPER_LOWER_LETTERS = METACLASS_DIGITS + METACLASS_UPPER_LOWER_LETTERS
WILDCARD_CHARACTERS_EXCLUDE = '[](|)\\'


def _count(subject: str, index: int, item: Union[Literal, Digit, Alphanumeric, Wildcard], target: Callable) -> Tuple[bool, int]:
    match = True

    if item.count == Count.One:
        try:
            if not target(subject[index]):
                match = False
            else:
                index += 1
        except IndexError:
            match = False
    elif item.count == Count.OneOrMore:
        count = 0

        for i in range(index, len(subject)):
            if not target(subject[i]):
                break

            count += 1

        if count < 1:
            match = False
        else:
            index += count
    elif item.count == Count.ZeroOrOne:
        try:
            if target(subject[index]):
                index += 1
        except IndexError:
            pass

    return match, index


def _match_item(item: Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup], index: int, subject: str) -> Tuple[bool, int]:
    match = True

    if isinstance(item, Literal):
        match, index = _count(subject, index, item, lambda c: c == item.value)
    elif isinstance(item, Digit):
        match, index = _count(subject, index, item, lambda c: c in METACLASS_DIGITS)
    elif isinstance(item, Alphanumeric):
        match, index = _count(subject, index, item, lambda c: c in METACLASS_DIGITS_UPPER_LOWER_LETTERS + '_')
    elif isinstance(item, CharacterSet):
        char = subject[index]

        if item.mode == CharacterSetMode.Positive and char not in item.values:
            match = False
        elif item.mode == CharacterSetMode.Negative and char in item.values:
            match = False
        else:
            index += 1
    elif isinstance(item, Wildcard):
        match, index = _count(subject, index, item, lambda c: c not in WILDCARD_CHARACTERS_EXCLUDE)
    elif isinstance(item, AlternationGroup):
        found = ''

        for choice in item.choices:
            chars = subject[index:index + len(choice)]

            if chars == choice:
                found = choice

                break

        if not found:
            match = False
        else:
            index += len(found)

    return match, index


class Matcher:
    pattern: Pattern
    subject: BytesIO

    def __init__(self, pattern: str, subject: str):
        self.pattern = Lexer(pattern).parse()
        self.subject = BytesIO(subject.encode())

    def match(self) -> bool:
        return False


def match_pattern(pattern: str, subject: str) -> bool:
    if not subject:
        raise ValueError('subject is empty')

    lexed_pattern = Lexer(pattern).parse()

    print(lexed_pattern)

    index = 0

    if not lexed_pattern.start:
        first_item = lexed_pattern.items.pop(0)

        first_match = False

        for i in range(0, len(subject)):
            match, index = _match_item(first_item, i, subject)

            if match:
                first_match = True

                break

        if not first_match:
            return False

    last_item = None

    if lexed_pattern.end:
        last_item = lexed_pattern.items.pop(-1)

    for item in lexed_pattern.items:
        match, index = _match_item(item, index, subject)

        if not match:
            return False

    if last_item:
        if index > len(subject) - 1:
            return False

        match, index = _match_item(last_item, index, subject)

        if not match or index != len(subject):
            return False

    return True