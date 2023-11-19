import string

DIGITS_CLASS = string.digits
LOWER_UPPER_LETTERS_CLASS = string.ascii_letters
LOWER_UPPER_LETTERS_DIGITS_CLASS = LOWER_UPPER_LETTERS_CLASS + DIGITS_CLASS + '_'


def match_pattern(pattern: str, subject: str) -> bool:
    index = 0

    while index <= len(pattern) - 1:
        char = pattern[index]

        print(index, char)

        if char == '\\': # Metaclass
            metaclass = pattern[index + 1]

            if metaclass == 'd' and not any(digit in subject for digit in DIGITS_CLASS): # Digits
                return False
            elif metaclass == 'w' and not any(alnum in subject for alnum in LOWER_UPPER_LETTERS_DIGITS_CLASS): # Alphanumeric
                return False

            index += 1
        elif char not in subject: # Literal character
            return False

        index += 1

    return True
