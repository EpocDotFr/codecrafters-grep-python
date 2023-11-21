from app.custom_types import CharacterGroupMode, Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation
from app.lexer import lex_pattern
from typing import Tuple, Union
import string

METACLASS_DIGITS = string.digits
METACLASS_UPPER_LOWER_LETTERS = string.ascii_letters
METACLASS_DIGITS_UPPER_LOWER_LETTERS = METACLASS_DIGITS + METACLASS_UPPER_LOWER_LETTERS


def _match_item(item: Union[Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation], index: int, subject: str) -> Tuple[bool, int]:
    match = True

    if isinstance(item, Literal):
        char = subject[index]

        if char != item.value:
            match = False
        else:
            index += 1
    elif isinstance(item, Digit):
        char = subject[index]

        if char not in METACLASS_DIGITS:
            match = False
        else:
            index += 1
    elif isinstance(item, Alphanumeric):
        char = subject[index]

        if char not in METACLASS_DIGITS_UPPER_LOWER_LETTERS + '_':
            match = False
        else:
            index += 1
    elif isinstance(item, CharacterGroup):
        char = subject[index]

        if item.mode == CharacterGroupMode.Positive and char not in item.values:
            match = False
        elif item.mode == CharacterGroupMode.Negative and char in item.values:
            match = False
        else:
            index += 1
    elif isinstance(item, Wildcard):
        # TODO?

        index += 1
    elif isinstance(item, Alternation):
        found = ''

        for choice in item.choices:
            length = len(choice)
            chars = subject[index:index + length]

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
        item = lexed_pattern.items.pop(0)

        first_match = False

        for i in range(0, len(subject)):
            match, index = _match_item(item, i, subject)

            if match:
                first_match = True

                break

        if not first_match:
            return False

    for item in lexed_pattern.items:
        match, index = _match_item(item, index, subject)

        if not match:
            return False

    if lexed_pattern.end and index < len(subject) - 1:
        return False

    return True
