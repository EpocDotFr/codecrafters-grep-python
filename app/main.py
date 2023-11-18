import argparse
import sys


def match_pattern(subject: str, pattern: str) -> bool:
    if len(pattern) == 1:
        return pattern in subject
    else:
        raise RuntimeError(f"Unhandled pattern: {pattern}")


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('pattern')
    arg_parser.add_argument('-E')

    args = arg_parser.parse_args()

    if match_pattern(sys.stdin.read().strip(), args.pattern):
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
