from app.custom_types import Count, CharacterSetMode, Pattern, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Group, GroupBackreference
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
    parsed_pattern: Pattern

    def __init__(self, pattern: str):
        start = end = False

        if pattern[0] == '^': # Start of string anchor
            start = True

            pattern = pattern[1:]

        if pattern[-1] == '$': # End of string anchor
            end = True

            pattern = pattern[:-1]

        self.pattern = BytesIO(pattern.encode())
        self.parsed_pattern = Pattern(start=start, end=end)

    def read_count(self, pattern: BytesIO) -> Count:
        pattern = pattern or self.pattern

        char = pattern.read(1)

        if not char:
            return Count.One

        try:
            return Count(char)
        except ValueError:
            pattern.seek(-1, SEEK_CUR)

            return Count.One

    def read_until(self, pattern: BytesIO, stop: bytes) -> bytes:
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

    def read_group_items(self, pattern: BytesIO) -> List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Group, GroupBackreference]]:
        items = []

        while True:
            char = pattern.read(1)

            if not char:
                break

            pattern.seek(-1, SEEK_CUR)

            items.extend(self.read_items(pattern))

        return items

    def read_items(self, pattern: Optional[BytesIO] = None) -> List[Union[Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, Group, GroupBackreference]]:
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
                    self.parsed_pattern.groups[reference - 1]
                except IndexError:
                    raise InvalidPattern(f'Group #{reference} does not exist') from None

                items.append(GroupBackreference(reference=reference))
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

            values = self.read_until(pattern, b']')

            count = self.read_count(pattern)

            items.append(
                CharacterSet(mode=mode, values=values, count=count)
            )
        elif char == b'.': # Wildcard
            count = self.read_count(pattern)

            items.append(Wildcard(count=count))
        elif char == b'(': # Groups
            content = self.read_until(pattern, b')')

            if b'|' in content: # Alternation
                choices = [
                    self.read_group_items(BytesIO(choice)) for choice in content.split(b'|')
                ]

                alternation_group = AlternationGroup(choices=choices)

                self.parsed_pattern.groups.append(alternation_group)

                items.append(alternation_group)
            else: # Regular group
                group_items = self.read_group_items(BytesIO(content))

                group = Group(items=group_items)

                self.parsed_pattern.groups.append(group)

                items.append(group)
        else: # Literal character
            count = self.read_count(pattern)

            items.append(
                Literal(value=char, count=count)
            )

        return items

    def parse(self) -> Pattern:
        while True:
            char = self.pattern.read(1)

            if not char:
                break

            self.pattern.seek(-1, SEEK_CUR)

            self.parsed_pattern.items.extend(self.read_items())

        return self.parsed_pattern
