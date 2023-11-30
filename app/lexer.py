from app.custom_types import Count, CharacterSetMode, Pattern, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, GroupBackreference, Group
from typing import List, Union, Optional
from io import BytesIO, SEEK_CUR
import string

# Full Codecrafter pattern that must be handled:
#
# ^ a \d \w \\ [abc] [^abc] a+ b? . (\w+) (cat|dog) \1 $
# | | ^^ ^^ ^^ ^^^^^ ^^^^^^  |  | | ^^^^^ ^^^^^^^^^ ^^ |
# | |  |  |  |   |     |     |  | |   |       |      | ∨
# | |  |  |  |   |     |     |  | |   |       |      |  End of string anchor
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
    p: BytesIO

    def __init__(self, pattern: str):
        self.p = BytesIO(pattern.encode())

    def read_count(self, p: Optional[BytesIO] = None) -> Count:
        p = p or self.p

        char = p.read(1)

        if not char:
            return Count.One

        try:
            return Count(char)
        except ValueError:
            p.seek(-1, SEEK_CUR)

            return Count.One

    def read_until(self, stop: bytes, p: Optional[BytesIO] = None) -> bytes:
        p = p or self.p

        value = b''
        end = False

        while True:
            char = p.read(1)

            if not char:
                break

            if char == stop:
                end = True

                break

            value += char

        if not end:
            raise InvalidPattern('Encountered EOF while parsing character group')

        return value

    def read_items(self, p: Optional[BytesIO] = None) -> List[Union[Digit, Alphanumeric, GroupBackreference, Literal, CharacterSet, Wildcard]]:
        p = p or self.p

        items = []

        char = p.read(1)

        if not char:
            return items

        if char == b'\\': # Metaclass
            metaclass = p.read(1)

            if not metaclass:
                raise InvalidPattern('Encountered EOF while parsing metaclass identifier')

            if metaclass in (b'd', b'w'):
                count = self.read_count(p)

                if metaclass == b'd': # Digit
                    items.append(Digit(count=count))
                elif metaclass == b'w': # Alphanumeric
                    items.append(Alphanumeric(count=count))
            elif metaclass in string.digits.encode(): # Group backreference
                items.append(GroupBackreference(reference=int(metaclass)))
            else: # Escaped backslash
                count = self.read_count(p)

                items.append(
                    Literal(value='\\', count=count)
                )
        elif char == b'[': # Positive or negative character set
            try:
                mode = CharacterSetMode(p.read(1))
            except ValueError:
                p.seek(-1, SEEK_CUR)

                mode = CharacterSetMode.Positive

            values = self.read_until(b']', p=p)

            items.append(
                CharacterSet(mode=mode, values=values.decode())
            )
        elif char == b'.': # Wildcard
            count = self.read_count(p)

            items.append(Wildcard(count=count))
        else: # Literal character
            count = self.read_count(p)

            items.append(
                Literal(value=char.decode(), count=count)
            )

        return items

    def parse(self) -> Pattern:
        start = end = False
        items = []

        while True:
            char = self.p.read(1)

            if not char:
                break

            if char == b'^': # Start of string anchor
                start = True
            elif char == b'$': # End of string anchor
                end = True
            elif char == b'(': # Groups
                content = self.read_until(b')')

                choices = content.decode().split('|')

                if len(choices) > 1: # Alternation
                    items.append(
                        AlternationGroup(choices=choices)
                    )
                else: # Regular group
                    items.append(
                        Group(items=self.read_items(BytesIO(content)))
                    )
            else:
                self.p.seek(-1, SEEK_CUR)

                items.extend(self.read_items())

        return Pattern(start=start, items=items, end=end)
