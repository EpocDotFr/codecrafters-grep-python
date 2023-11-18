import string


def match_pattern(pattern: str, subject: str) -> bool:
    index = 0

    while index <= len(pattern) - 1:
        char = pattern[index]

        print(index, char)

        if char == '\\':
            metaclass = pattern[index + 1]

            if metaclass == 'd' and not any(digit in subject for digit in string.digits): # Digits
                return False

            index += 1
        elif char not in subject: # Literal character
            return False

        index += 1

    return True
