from app.custom_types import Count, CharacterSetMode, Pattern, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Group
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
    groups: List[Group] = []

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

    def read_items(self, pattern: Optional[BytesIO] = None) -> List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard]]:
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
                reference = int(metaclass)

                try:
                    items.append(self.groups[reference - 1])
                except IndexError:
                    raise InvalidPattern(f'Group #{reference} does not exist') from None
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

            count = self.read_count(pattern)

            items.append(
                CharacterSet(mode=mode, values=values, count=count)
            )
        elif char == b'.': # Wildcard
            count = self.read_count(pattern)

            items.append(Wildcard(count=count))
        elif char == b'(': # Groups
            content = self.read_until(b')', pattern=pattern)

            if b'|' in content: # Alternation
                items.append(
                    AlternationGroup(choices=content.split(b'|'))
                )
            else: # Regular group
                group_items = []
                group_pattern = BytesIO(content)

                while True:
                    group_char = group_pattern.read(1)

                    if not group_char:
                        break

                    group_pattern.seek(-1, SEEK_CUR)

                    group_items.extend(self.read_items(group_pattern))

                group = Group(items=group_items)

                self.groups.append(group)

                items.append(group)
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
            else:
                self.pattern.seek(-1, SEEK_CUR)

                items.extend(self.read_items())

        return Pattern(start=start, items=items, end=end)
