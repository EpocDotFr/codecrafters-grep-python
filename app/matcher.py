from app.custom_types import Count, CharacterSetMode, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Pattern
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

        print(self.pattern)

    def match_count(self, item: Union[Literal, Digit, Alphanumeric, Wildcard], target: Callable) -> bool:
        if item.count == Count.One:
            if not target(self.subject.read(1)):
                return False
        elif item.count == Count.OneOrMore:
            count = 0

            while True:
                char = self.subject.read(1)

                if not char or not target(char):
                    self.subject.seek(-1, SEEK_CUR)

                    break

                count += 1

            if count < 1:
                return False
        elif item.count == Count.ZeroOrOne:
            char = self.subject.read(1)

            if char and not target(char):
                self.subject.seek(-1, SEEK_CUR)

        return True

    def match_item(self, item: Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup]) -> bool:
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
            char = self.subject.read(1)

            if item.mode == CharacterSetMode.Positive and char not in item.values:
                return False
            elif item.mode == CharacterSetMode.Negative and char in item.values:
                return False
        elif isinstance(item, Wildcard):
            if not self.match_count(item, lambda c: c not in WILDCARD_CHARACTERS_EXCLUDE):
                return False
        elif isinstance(item, AlternationGroup):
            old_pos = self.subject.tell()
            found = False

            for choice in item.choices:
                found = self.subject.read(len(choice)) == choice

                if found:
                    break

                self.subject.seek(old_pos)

            if not found:
                return False

        return True

    def match(self) -> bool:
        if not self.pattern.start:
            first_item = self.pattern.items.pop(0)

            while True:
                if not self.subject.read(1):  # Subject has been completely read
                    return False

                self.subject.seek(-1, SEEK_CUR)

                first_match = self.match_item(first_item)

                if first_match:
                    break

            if not first_match:
                return False

        last_item = self.pattern.items.pop(-1) if self.pattern.end else None

        for item in self.pattern.items:
            match = self.match_item(item)

            if not match:
                return False

        if last_item:
            if not self.subject.read(1): # Subject has been completely read
                return False

            self.subject.seek(-1, SEEK_CUR)

            match = self.match_item(last_item)

            if not match:
                return False

            if self.subject.read(1): # Matched but subject has not been completely read
                return False

        return True
