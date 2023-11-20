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

            try:
                count = Count(pattern[index + 2])
            except (IndexError, ValueError):
                count = Count.One

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

            values = ''
            gend = False

            for i in range(index, len(pattern)):
                gchar = pattern[i]

                if gchar == ']':
                    gend = True

                    break

                values += gchar

            if not gend:
                raise InvalidPattern('Encountered EOF while parsing character group')

            items.append(
                CharacterGroup(mode=mode, values=values)
            )

            index += len(values)
        elif char == '(': # Alternation
            index += 1

            value = ''
            aend = False

            for i in range(index, len(pattern)):
                achar = pattern[i]

                if achar == ')':
                    aend = True

                    break

                value += achar

            if not aend:
                raise InvalidPattern('Encountered EOF while parsing character group')

            items.append(
                Alternation(choices=value.split('|'))
            )

            index += len(value)
        elif char == '.': # Wildcard
            try:
                count = Count(pattern[index + 1])
            except (IndexError, ValueError):
                count = Count.One

            items.append(Wildcard(count=count))

            if count != count.One:
                index += 1
        else: # Literal character
            try:
                count = Count(pattern[index + 1])
            except (IndexError, ValueError):
                count = Count.One

            items.append(
                Literal(value=char, count=count)
            )

            if count != count.One:
                index += 1

        index += 1

    return Pattern(start=start, items=items, end=end)
