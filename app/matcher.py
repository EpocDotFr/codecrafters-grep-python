from app.custom_types import CharacterGroupMode, Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation
from app.lexer import lex_pattern
import string

METACLASS_DIGITS = string.digits
METACLASS_UPPER_LOWER_LETTERS = string.ascii_letters
METACLASS_DIGITS_UPPER_LOWER_LETTERS = METACLASS_DIGITS + METACLASS_UPPER_LOWER_LETTERS


def match_pattern(pattern: str, subject: str) -> bool:
    if not subject:
        raise ValueError('subject is empty')

    lexed_pattern = lex_pattern(pattern)

    print(lexed_pattern)

    # TODO Non-start-of-string mode: pop first item, and try to match by incrementing the index

    index = 0

    for item in lexed_pattern.items:
        if isinstance(item, Literal):
            char = subject[index]

            if char != item.value:
                return False

            index += 1
        elif isinstance(item, Digit):
            char = subject[index]

            if char not in METACLASS_DIGITS:
                return False

            index += 1
        elif isinstance(item, Alphanumeric):
            char = subject[index]

            if char not in METACLASS_DIGITS_UPPER_LOWER_LETTERS + '_':
                return False

            index += 1
        elif isinstance(item, CharacterGroup):
            match = any([
                c in subject for c in item.values
            ])

            if item.mode == CharacterGroupMode.Positive and not match:
                return False
            elif item.mode == CharacterGroupMode.Negative and match:
                return False

            # char = subject[index]
            #
            # if item.mode == CharacterGroupMode.Positive and char not in item.values:
            #     return False
            # elif item.mode == CharacterGroupMode.Negative and char in item.values:
            #     return False

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
                return False

            index += len(found)

    return True
