from app.custom_types import Count, CharacterSetMode, Pattern, Literal, Digit, Alphanumeric, CharacterSet, Wildcard, AlternationGroup, GroupBackreference
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

    def read_count(self) -> Count:
        char = self.p.read(1)

        if not char:
            return Count.One

        try:
            return Count(char)
        except ValueError:
            self.p.seek(-1, SEEK_CUR)

            return Count.One

    def read_until(self, stop: bytes) -> bytes:
        value = b''
        end = False

        while True:
            char = self.p.read(1)

            if not char:
                break

            if char == stop:
                end = True

                break

            value += char

        if not end:
            raise InvalidPattern('Encountered EOF while parsing character group')

        return value

    def parse(self) -> Pattern:
        start = end = False
        items = []

        while True:
            char = self.p.read(1)

            if not char:
                break

            if char == b'^': # Start of string anchor
                start = True
            elif char == b'\\': # Metaclass
                metaclass = self.p.read(1)

                if not metaclass:
                    raise InvalidPattern('Encountered EOF while parsing metaclass identifier')

                if metaclass in (b'd', b'w'):
                    count = self.read_count()

                    if count is None:
                        break

                    if metaclass == b'd': # Digit
                        items.append(Digit(count=count))
                    elif metaclass == b'w': # Alphanumeric
                        items.append(Alphanumeric(count=count))
                elif metaclass in string.digits.encode(): # Group backreference
                    items.append(GroupBackreference(reference=int(metaclass)))
                else: # Escaped backslash
                    count = self.read_count()

                    if count is None:
                        break

                    items.append(
                        Literal(value='\\', count=count)
                    )
            elif char == b'[': # Positive or negative character set
                try:
                    mode = CharacterSetMode(self.p.read(1))
                except ValueError:
                    self.p.seek(-1, SEEK_CUR)

                    mode = CharacterSetMode.Positive

                values = self.read_until(b']')

                items.append(
                    CharacterSet(mode=mode, values=values.decode())
                )
            elif char == b'(': # Group
                content = self.read_until(b')')

                choices = content.split(b'|')

                if len(choices) > 1: # Alternation
                    items.append(
                        AlternationGroup(choices=[choice.decode() for choice in choices])
                    )
                else:
                    pass
            elif char == b'.': # Wildcard
                count = self.read_count()

                if count is None:
                    break

                items.append(Wildcard(count=count))
            elif char == b'$': # End of string anchor
                end = True
            else: # Literal character
                count = self.read_count()

                if count is None:
                    break

                items.append(
                    Literal(value=char.decode(), count=count)
                )

        return Pattern(start=start, items=items, end=end)
