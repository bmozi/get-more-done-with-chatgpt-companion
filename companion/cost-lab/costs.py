"""Compare two complete fictional monthly plans. Standard library only."""
import argparse
import json


def compare(visits, fixed_a=20, per_a=4, per_b=8):
    for name, value in [('visits', visits), ('fixed_a', fixed_a), ('per_a', per_a), ('per_b', per_b)]:
        if type(value) is not int or value < 0:
            raise ValueError(name + ' must be a nonnegative whole number')
    a, b = fixed_a + per_a * visits, per_b * visits
    return {'visits': visits, 'plan_A': a, 'plan_B': b,
            'winner': 'A' if a < b else 'B' if b < a else None,
            'currency': 'USD', 'period': 'month', 'fictional': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--visits', type=int, required=True)
    args = parser.parse_args()
    try:
        result = compare(args.visits)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
