"""Stop unexplained Mohist/Banner removals; never resurrect unverified URLs."""
import argparse
from pathlib import Path
from preserve_pufferfish import read_snapshot, package_key

CATEGORIES = {"Mohist", "Banner"}
# Review upstream availability before adding an intentional retirement here.
RETIRED_PACKAGES: set[tuple[str, str]] = set()


def validate(previous_path, current_path):
    previous = read_snapshot(previous_path)
    current = read_snapshot(current_path)
    keys = {package_key(p) for p in current['packages']}
    missing_categories = CATEGORIES - {key[0] for key in keys}
    removed = {package_key(p) for p in previous['packages']
               if p['category'] in CATEGORIES} - keys - RETIRED_PACKAGES
    if missing_categories or removed:
        raise ValueError(f"Refusing Mohist/Banner data loss: missing cores={sorted(missing_categories)}, "
                         f"removed packages={sorted(removed)}. Review upstream availability first.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('previous', type=Path)
    parser.add_argument('current', type=Path)
    args = parser.parse_args()
    validate(args.previous, args.current)
