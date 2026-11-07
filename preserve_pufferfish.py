import argparse
import json
from pathlib import Path


PROTECTED_CATEGORIES = {"Pufferfish", "Pufferfish+", "Pufferfish+Purpur"}
# Add reviewed (category, title) pairs here to remove them from future releases.
RETIRED_PACKAGES: set[tuple[str, str]] = set()


def package_key(package):
    return package["category"], package["title"]


def read_snapshot(path):
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("packages"), list):
        raise ValueError(f"{path}: expected a packages list")
    for package in snapshot["packages"]:
        if not isinstance(package, dict) or not all(
            isinstance(package.get(field), str) and package[field]
            for field in ("category", "title")
        ):
            raise ValueError(f"{path}: invalid package identity")
    return snapshot


def preserve_pufferfish(previous_path, current_path):
    previous = read_snapshot(previous_path)
    current = read_snapshot(current_path)
    packages = [
        package for package in current["packages"]
        if package_key(package) not in RETIRED_PACKAGES
    ]
    present = {package_key(package) for package in packages}

    for package in previous["packages"]:
        key = package_key(package)
        if key[0] in PROTECTED_CATEGORIES and key not in present and key not in RETIRED_PACKAGES:
            packages.append(package)
            present.add(key)
            print(f"Retained previously published package: {key[1]}")

    if packages != current["packages"]:
        current["packages"] = packages
        current_path.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("previous", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()
    preserve_pufferfish(args.previous, args.current)
