from app.matcher import Matcher
import argparse
import sys


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('pattern')

    args, _ = arg_parser.parse_known_args()
    subject = sys.stdin.read()

    matcher = Matcher(args.pattern, subject)

    matching = matcher.match()

    print(matcher.pattern)

    print('Yep' if matching else 'Nope')

    exit(0 if matching else 1)


if __name__ == '__main__':
    main()
