from app.custom_types import Count, CharacterGroupMode, Pattern, Literal, Digit, Alphanumeric, CharacterGroup, Wildcard, Alternation

# Full Codecrafter pattern that must be handled:
#
# ^ a \d \w [abc] [^abc] a+ b? . (cat|dog) $
# | | ^^ ^^ ^^^^^ ^^^^^^  |  | | ^^^^^^^^^ |
# | |  |  |   |     |     |  | |     |     ∨
# | |  |  |   |     |     |  | |     ∨     End of string anchor
# | |  |  |   |     |     |  | ∨     Alternation
# | |  |  |   |     |     |  ∨ Wildcard
# | |  |  |   |     |     ∨  Zero or one
# | |  |  |   |     ∨     One or more
# | |  |  |   ∨     Negative character group
# | |  |  ∨   Positive character group
# | |  ∨  Alphanumeric
# | ∨  Digit
# ∨ Literal character
# Start of string anchor

class InvalidPattern(Exception):
    pass


def _lex_count(pattern: str, index: int) -> Count:
    try:
        return Count(pattern[index])
    except (IndexError, ValueError):
        return Count.One


def _read_until(pattern: str, index: int, stop: str) -> str:
    value = ''
    end = False

    for i in range(index, len(pattern)):
        char = pattern[i]

        if char == stop:
            end = True

            break

        value += char

    if not end:
        raise InvalidPattern('Encountered EOF while parsing character group')

    return value


def lex_pattern(pattern: str) -> Pattern:
    if not pattern:
        raise InvalidPattern('pattern is empty')

    start = pattern[0] == '^'

    try:
        end = pattern[-1] == '$'
    except IndexError:
        end = False

    pattern = pattern.strip('^$')

    items = []
    index = 0

    while index <= len(pattern) - 1:
        char = pattern[index]

        if char == '\\': # Metaclass
            try:
                metaclass = pattern[index + 1]
            except IndexError:
                raise InvalidPattern('Encountered EOF while parsing metaclass identifier') from None

            count = _lex_count(pattern, index + 2)

            if metaclass == 'd': # Digit
                items.append(Digit(count=count))
            elif metaclass == 'w': # Alphanumeric
                items.append(Alphanumeric(count=count))

            index += 1 if count == Count.One else 2
        elif char == '[': # Positive or negative character group
            try:
                mode = CharacterGroupMode(pattern[index + 1])
            except (IndexError, ValueError):
                mode = CharacterGroupMode.Positive

            index += 2 if mode == CharacterGroupMode.Negative else 1

            values = _read_until(pattern, index, ']')

            items.append(
                CharacterGroup(mode=mode, values=values)
            )

            index += len(values)
        elif char == '(': # Alternation
            index += 1

            choices = _read_until(pattern, index, ')')

            items.append(
                Alternation(choices=choices.split('|'))
            )

            index += len(choices)
        elif char == '.': # Wildcard
            count = _lex_count(pattern, index + 1)

            items.append(Wildcard(count=count))

            if count != count.One:
                index += 1
        else: # Literal character
            count = _lex_count(pattern, index + 1)

            items.append(
                Literal(value=char, count=count)
            )

            if count != count.One:
                index += 1

        index += 1

    return Pattern(start=start, items=items, end=end)
