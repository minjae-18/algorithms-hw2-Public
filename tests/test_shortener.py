import unittest

import src.shortener as shortener_module
from src.base62 import decode
from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable
from src.shortener import expand, shorten


class ShortenerTestMixin:
    strategy = "chaining"

    def setUp(self):
        shortener_module._url_to_id = HashTable()
        shortener_module._id_to_url = HashTable()
        shortener_module._next_id = 0
        shortener_module._table_strategy = "chaining"
        shortener_module.configure_hash_table(self.strategy)

    def test_shortens_and_expands_urls_with_sequential_codes(self):
        first_url = "https://example.com/path?query=value#section"
        second_url = "http://example.org"

        self.assertEqual(shorten(first_url), "0")
        self.assertEqual(shorten(second_url), "1")
        self.assertEqual(expand("0"), first_url)
        self.assertEqual(expand("1"), second_url)
        self.assertEqual(shortener_module._id_to_url.get("0"), first_url)
        self.assertEqual(shortener_module._id_to_url.get("1"), second_url)

    def test_repeated_url_returns_existing_code_without_consuming_an_id(self):
        url = "https://example.com"

        self.assertEqual(shorten(url), "0")
        self.assertEqual(shorten(url), "0")
        self.assertEqual(shorten("https://example.com/"), "1")

    def test_codes_use_base62_after_decimal_id_61(self):
        for index in range(63):
            code = shorten(f"https://example.com/{index}")
            self.assertEqual(decode(code), index)

        self.assertEqual(shorten("https://example.com/61"), "Z")
        self.assertEqual(shorten("https://example.com/62"), "10")
        self.assertEqual(expand("Z"), "https://example.com/61")
        self.assertEqual(expand("10"), "https://example.com/62")

    def test_accepts_valid_schemes_hosts_and_port_boundaries(self):
        urls = [
            "http://example.com",
            "https://example.com:1/path",
            "https://example.com:65535/path",
            "https://localhost",
        ]

        for url in urls:
            with self.subTest(url=url):
                code = shorten(url)
                self.assertEqual(expand(code), url)

    def test_rejects_non_string_url(self):
        with self.assertRaises(TypeError):
            shorten(None)

    def test_rejects_invalid_urls(self):
        urls = [
            "",
            "/relative/path",
            "//example.com/path",
            "ftp://example.com",
            "http:///path",
            "https://",
            " https://example.com",
            "https://example.com ",
            "https://exa mple.com",
            "https://example.com/a\tb",
            "https://example.com/\n",
            "https://example.com/\x00",
            "https://example.com:0",
            "https://example.com:65536",
            "https://example.com:abc",
            "https://example.com:",
            "https://[::1",
        ]

        for url in urls:
            with self.subTest(url=repr(url)):
                with self.assertRaises(ValueError):
                    shorten(url)

        self.assertEqual(shorten("https://example.com/valid"), "0")

    def test_rejects_non_string_empty_and_invalid_codes(self):
        with self.assertRaises(TypeError):
            expand(None)
        with self.assertRaises(ValueError):
            expand("")
        with self.assertRaises(ValueError):
            expand("0!")
        with self.assertRaises(ValueError):
            expand("é")

    def test_valid_but_unregistered_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            expand("0")


class ChainingShortenerTests(ShortenerTestMixin, unittest.TestCase):
    pass


class LinearProbingShortenerTests(ShortenerTestMixin, unittest.TestCase):
    strategy = "linear-probing"


class ShortenerStrategyTests(unittest.TestCase):
    def setUp(self):
        shortener_module._url_to_id = HashTable()
        shortener_module._id_to_url = HashTable()
        shortener_module._next_id = 0
        shortener_module._table_strategy = "chaining"

    def test_switching_strategies_preserves_mappings_and_rejects_unknown(self):
        self.assertEqual(shorten("https://example.com"), "0")
        self.assertEqual(shorten("https://example.org"), "1")

        shortener_module.configure_hash_table("linear-probing")
        self.assertIsInstance(shortener_module._url_to_id, LinearProbingHashTable)
        self.assertEqual(shorten("https://example.com"), "0")
        self.assertEqual(expand("1"), "https://example.org")
        self.assertEqual(shorten("https://example.net"), "2")

        shortener_module.configure_hash_table("chaining")
        self.assertIsInstance(shortener_module._url_to_id, HashTable)
        self.assertEqual(expand("2"), "https://example.net")
        with self.assertRaises(ValueError):
            shortener_module.configure_hash_table("unknown")


if __name__ == "__main__":
    unittest.main()
