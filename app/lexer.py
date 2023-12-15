from app.custom_types import Count, CharacterSetMode, Pattern, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, GroupBackreference, Group
from typing import List, Union, Optional
from io import BytesIO, SEEK_CUR
import string

# Full Codecrafter pattern that must be handled:
#
# ^ a \d \w \\ [abc] [^abc] a+ b? . (\w+) (cat|dog) \1 $
# | | ^^ ^^ ^^ ^^^^^ ^^^^^^  |  | | ^^^^^ ^^^^^^^^^ ^^ |
# | |  |  |  |   |     |     |  | |   |       |      | ∨
# | |  |  |  |   |     |     |  | |   |       |      ∨ End of string anchor
# | |  |  |  |   |     |     |  | |   |       ∨      Group backreference
# | |  |  |  |   |     |     |  | |   ∨       Alternation group
# | |  |  |  |   |     |     |  | ∨   Group
# | |  |  |  |   |     |     |  ∨ Wildcard
# | |  |  |  |   |     |     ∨  Zero or one
# | |  |  |  |   |     ∨     One or more
# | |  |  |  |   ∨     Negative character group
# | |  |  |  ∨   Positive character group
# | |  |  ∨  Escaped backslash
# | |  ∨  Alphanumeric
# | ∨  Digit
# ∨ Literal character
# Start of string anchor

class InvalidPattern(Exception):
    pass


class Lexer:
    pattern: BytesIO

    def __init__(self, pattern: str):
        self.pattern = BytesIO(pattern.encode())

    def read_count(self, pattern: Optional[BytesIO] = None) -> Count:
        pattern = pattern or self.pattern

        char = pattern.read(1)

        if not char:
            return Count.One

        try:
            return Count(char)
        except ValueError:
            pattern.seek(-1, SEEK_CUR)

            return Count.One

    def read_until(self, stop: bytes, pattern: Optional[BytesIO] = None) -> bytes:
        pattern = pattern or self.pattern

        value = b''
        end = False

        while True:
            char = pattern.read(1)

            if not char:
                break

            if char == stop:
                end = True

                break

            value += char

        if not end:
            raise InvalidPattern('Encountered EOF while parsing character group')

        return value

    def read_items(self, pattern: Optional[BytesIO] = None) -> List[Union[Literal, Digit, Alphanumeric, GroupBackreference, CharacterSet, Wildcard]]:
        pattern = pattern or self.pattern

        items = []

        char = pattern.read(1)

        if not char:
            return items

        if char == b'\\': # Metaclass
            metaclass = pattern.read(1)

            if not metaclass:
                raise InvalidPattern('Encountered EOF while parsing metaclass identifier')

            if metaclass in (b'd', b'w'):
                count = self.read_count(pattern)

                if metaclass == b'd': # Digit
                    items.append(Digit(count=count))
                elif metaclass == b'w': # Alphanumeric
                    items.append(Alphanumeric(count=count))
            elif metaclass in string.digits.encode(): # Group backreference
                items.append(GroupBackreference(reference=int(metaclass)))
            else: # Escaped backslash
                count = self.read_count(pattern)

                items.append(
                    Literal(value=b'\\', count=count)
                )
        elif char == b'[': # Positive or negative character set
            try:
                mode = CharacterSetMode(pattern.read(1))
            except ValueError:
                pattern.seek(-1, SEEK_CUR)

                mode = CharacterSetMode.Positive

            values = self.read_until(b']', pattern=pattern)

            items.append(
                CharacterSet(mode=mode, values=values)
            )
        elif char == b'.': # Wildcard
            count = self.read_count(pattern)

            items.append(Wildcard(count=count))
        else: # Literal character
            count = self.read_count(pattern)

            items.append(
                Literal(value=char, count=count)
            )

        return items

    def parse(self) -> Pattern:
        start = end = False
        items = []

        while True:
            char = self.pattern.read(1)

            if not char:
                break

            if char == b'^': # Start of string anchor
                start = True
            elif char == b'$': # End of string anchor
                end = True
            elif char == b'(': # Groups
                content = self.read_until(b')')

                choices = content.split(b'|')

                if len(choices) > 1: # Alternation
                    items.append(
                        AlternationGroup(choices=choices)
                    )
                else: # Regular group
                    items.append(
                        Group(items=self.read_items(BytesIO(content)))
                    )
            else:
                self.pattern.seek(-1, SEEK_CUR)

                items.extend(self.read_items())

        return Pattern(start=start, items=items, end=end)
