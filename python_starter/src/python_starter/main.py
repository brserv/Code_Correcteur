import sys


def greet(name: str) -> str:
    return f"Hello, {name}!"


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    name = argv[0] if argv else "World"
    print(greet(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
