from app.custom_types import Count, CharacterSetMode, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Pattern, Group, GroupBackreference
from typing import Union, Callable
from io import BytesIO, SEEK_CUR
from app.lexer import Lexer
import string

METACLASS_DIGITS = string.digits.encode()
METACLASS_UPPER_LOWER_LETTERS = string.ascii_letters.encode()
METACLASS_DIGITS_UPPER_LOWER_LETTERS = METACLASS_DIGITS + METACLASS_UPPER_LOWER_LETTERS
WILDCARD_CHARACTERS_EXCLUDE = b'[](|)\\'


class Matcher:
    pattern: Pattern
    subject: BytesIO

    def __init__(self, pattern: str, subject: str):
        self.pattern = Lexer(pattern).parse()
        self.subject = BytesIO(subject.encode())

    def match_count(self, item: Union[Literal, Digit, Alphanumeric, Wildcard, CharacterSet], target: Callable) -> bool:
        if item.count == Count.One:
            char = self.subject.read(1)

            if not char or not target(char):
                return False

            item.matched = char
        elif item.count == Count.OneOrMore:
            count = 0
            empty = False
            chars = b''

            while True:
                char = self.subject.read(1)

                if not char or not target(char):
                    if not char:
                        empty = True

                    break

                chars += char
                count += 1

            if count < 1:
                return False

            if not empty:
                self.subject.seek(-1, SEEK_CUR)

            item.matched = chars
        elif item.count == Count.ZeroOrOne:
            char = self.subject.read(1)

            if char:
                if not target(char):
                    self.subject.seek(-1, SEEK_CUR)
                else:
                    item.matched = char

        return True

    def match_item(self, item: Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Group, GroupBackreference]) -> bool:
        if isinstance(item, Literal):
            if not self.match_count(item, lambda c: c == item.value):
                return False
        elif isinstance(item, Digit):
            if not self.match_count(item, lambda c: c in METACLASS_DIGITS):
                return False
        elif isinstance(item, Alphanumeric):
            if not self.match_count(item, lambda c: c in METACLASS_DIGITS_UPPER_LOWER_LETTERS + b'_'):
                return False
        elif isinstance(item, CharacterSet):
            if item.mode == CharacterSetMode.Positive and not self.match_count(item, lambda c: c in item.values):
                return False
            elif item.mode == CharacterSetMode.Negative and not self.match_count(item, lambda c: c not in item.values):
                return False
        elif isinstance(item, Wildcard):
            if not self.match_count(item, lambda c: c not in WILDCARD_CHARACTERS_EXCLUDE):
                return False
        elif isinstance(item, AlternationGroup):
            old_pos = self.subject.tell()
            matched_choice = None

            for i, choices in enumerate(item.choices):
                group_found = True

                for choice_item in choices:
                    if not self.match_item(choice_item):
                        group_found = False

                        break

                if group_found:
                    matched_choice = i

                    break
                elif i < len(item.choices) - 1:
                    self.subject.seek(old_pos)

            if matched_choice is None:
                return False

            item.matched_choice = matched_choice
        elif isinstance(item, Group):
            for group_item in item.items:
                if not self.match_item(group_item):
                    return False
        elif isinstance(item, GroupBackreference):
            should_match = self.pattern.groups[item.reference - 1].matched
            chars = self.subject.read(len(should_match))

            if chars != should_match:
                return False

        return True

    def match(self) -> bool:
        if not self.pattern.start:
            first_item = self.pattern.items[0]

            while True:
                if not self.subject.read(1):  # Subject has been completely read
                    return False

                self.subject.seek(-1, SEEK_CUR)

                first_match = self.match_item(first_item)

                if first_match:
                    break

            if not first_match:
                return False

        for item in self.pattern.items[slice(1 if not self.pattern.start else None, -1 if self.pattern.end else None)]:
            match = self.match_item(item)

            if not match:
                return False

        if self.pattern.end:
            last_item = self.pattern.items[-1]

            if not self.subject.read(1): # Subject has been completely read
                return False

            self.subject.seek(-1, SEEK_CUR)

            match = self.match_item(last_item)

            if not match:
                return False

            if self.subject.read(1): # Matched but subject has not been completely read
                return False

        return True
