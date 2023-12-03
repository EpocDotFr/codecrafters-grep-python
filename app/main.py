from app.matcher import Matcher, match_pattern
import argparse
import sys


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('pattern')

    args, _ = arg_parser.parse_known_args()
    subject = sys.stdin.read()

    matching = match_pattern(args.pattern, subject)

    print('Yep' if matching else 'Nope')
    print('New', 'Yep' if Matcher(args.pattern, subject).match() else 'Nope')

    exit(0 if matching else 1)


if __name__ == '__main__':
    main()
