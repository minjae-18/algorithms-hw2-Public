"""Base62 conversion using digits, lowercase letters, then uppercase letters."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(n: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return ALPHABET[0]

    encoded = []
    while n:
        n, remainder = divmod(n, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(s: str) -> int:
    """Decode a base62 string to a non-negative integer."""
    if not isinstance(s, str):
        raise TypeError("s must be a string")
    if not s:
        raise ValueError("s must not be empty")

    value = 0
    for char in s:
        try:
            digit = ALPHABET.index(char)
        except ValueError:
            raise ValueError(f"invalid base62 character: {char!r}") from None
        value = value * BASE + digit
    return value
