"""In-memory URL shortening built on the project's base62 and hash table."""

import unicodedata
from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


_url_to_id = HashTable()
_id_to_url = HashTable()
_next_id = 0
_table_strategy = "chaining"


def configure_hash_table(strategy: str) -> None:
    """Select a hash-table implementation, preserving existing mappings."""
    global _url_to_id, _id_to_url, _table_strategy

    if strategy == "chaining":
        table_type = HashTable
    elif strategy == "linear-probing":
        table_type = LinearProbingHashTable
    else:
        raise ValueError("strategy must be 'chaining' or 'linear-probing'")

    if strategy == _table_strategy:
        return

    url_table = table_type()
    id_table = table_type()
    for key, value in _url_to_id._iter_items():
        url_table.insert(key, value)
    for key, value in _id_to_url._iter_items():
        id_table.insert(key, value)
    _url_to_id = url_table
    _id_to_url = id_table
    _table_strategy = strategy


def _validate_url(url: str) -> None:
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if any(character.isspace() or unicodedata.category(character) == "Cc" for character in url):
        raise ValueError("url must not contain whitespace or control characters")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError("url must be a valid absolute HTTP or HTTPS URL") from None

    if parsed.scheme not in ("http", "https") or not parsed.netloc or not hostname:
        raise ValueError("url must be a valid absolute HTTP or HTTPS URL with a hostname")

    authority = parsed.netloc.rsplit("@", 1)[-1]
    if authority.startswith("["):
        closing_bracket = authority.find("]")
        port_is_explicit = authority[closing_bracket + 1 :].startswith(":")
    else:
        port_is_explicit = ":" in authority

    if port_is_explicit and port is None:
        raise ValueError("url port must be an integer from 1 to 65535")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("url port must be an integer from 1 to 65535")


def shorten(url: str) -> str:
    """Return a stable base62 code for an absolute HTTP or HTTPS URL."""
    global _next_id

    _validate_url(url)
    existing_id = _url_to_id.get(url)
    if existing_id is not None:
        return encode(existing_id)

    identifier = _next_id
    _url_to_id.insert(url, identifier)
    _id_to_url.insert(str(identifier), url)
    _next_id += 1
    return encode(identifier)


def expand(code: str) -> str:
    """Return the URL assigned to a base62 code."""
    identifier = decode(code)
    url = _id_to_url.get(str(identifier))
    if url is None:
        raise KeyError(code)
    return url
