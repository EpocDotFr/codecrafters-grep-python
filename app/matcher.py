from app.custom_types import Count, CharacterGroupMode, Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation
from typing import Tuple, Union, Callable
from app.lexer import lex_pattern
import string

METACLASS_DIGITS = string.digits
METACLASS_UPPER_LOWER_LETTERS = string.ascii_letters
METACLASS_DIGITS_UPPER_LOWER_LETTERS = METACLASS_DIGITS + METACLASS_UPPER_LOWER_LETTERS
WILDCARD_CHARACTERS_EXCLUDE = '[](|)\\'


def _count(subject: str, index: int, item: Union[Literal, Digit, Alphanumeric, Wildcard], target: Callable) -> Tuple[bool, int]:
    match = False
    count = 0

    for i in range(index, len(subject)):
        if target(subject[i]):
            count += 1

        if item.count == Count.One and count == 1:
            match = True

            break
        elif item.count == Count.OneOrMore and count >= 1:
            match = True

            break
        elif item.count == Count.ZeroOrOne and count in (0, 1):
            match = True

            break

    if match:
        index += count

    return match, index


def _match_item(item: Union[Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation], index: int, subject: str) -> Tuple[bool, int]:
    match = True

    if isinstance(item, Literal):
        match, index = _count(subject, index, item, lambda c: c == item.value)
    elif isinstance(item, Digit):
        match, index = _count(subject, index, item, lambda c: c in METACLASS_DIGITS)
    elif isinstance(item, Alphanumeric):
        match, index = _count(subject, index, item, lambda c: c in METACLASS_DIGITS_UPPER_LOWER_LETTERS + '_')
    elif isinstance(item, CharacterGroup):
        char = subject[index]

        if item.mode == CharacterGroupMode.Positive and char not in item.values:
            match = False
        elif item.mode == CharacterGroupMode.Negative and char in item.values:
            match = False
        else:
            index += 1
    elif isinstance(item, Wildcard):
        match, index = _count(subject, index, item, lambda c: c not in WILDCARD_CHARACTERS_EXCLUDE)
    elif isinstance(item, Alternation):
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


def match_pattern(pattern: str, subject: str) -> bool:
    if not subject:
        raise ValueError('subject is empty')

    lexed_pattern = lex_pattern(pattern)

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
        if index > len(subject) - 1:
            return False

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