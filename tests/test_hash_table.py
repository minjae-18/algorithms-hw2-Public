import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_returns_none(self):
        table = HashTable()

        self.assertEqual(table.capacity, 8)
        self.assertEqual(table.size, 0)
        self.assertIsNone(table.get("missing"))

    def test_colliding_keys_can_be_inserted_and_retrieved(self):
        table = HashTable()
        keys = ["a", "i", "q"]

        for index, key in enumerate(keys):
            self.assertTrue(table.insert(key, index))

        self.assertEqual([table.get(key) for key in keys], [0, 1, 2])
        self.assertEqual(table.size, 3)

    def test_duplicate_key_does_not_replace_value_or_increase_size(self):
        table = HashTable()

        self.assertTrue(table.insert("key", "original"))
        self.assertFalse(table.insert("key", "replacement"))

        self.assertEqual(table.get("key"), "original")
        self.assertEqual(table.size, 1)

    def test_table_resizes_after_load_exceeds_three_quarters(self):
        table = HashTable()
        for index in range(6):
            self.assertTrue(table.insert(f"key-{index}", index))
        self.assertEqual(table.capacity, 8)

        self.assertTrue(table.insert("key-6", 6))

        self.assertEqual(table.capacity, 16)
        self.assertEqual(table.size, 7)
        for index in range(7):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_table_uses_configured_maximum_load_factor(self):
        table = HashTable(max_load_factor=0.5)

        for index in range(5):
            self.assertTrue(table.insert(f"key-{index}", index))

        self.assertEqual(table.capacity, 16)
        self.assertEqual(table.size, 5)
        for index in range(5):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_maximum_load_factor_must_be_finite_and_positive(self):
        for value in (0, -0.5, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    HashTable(max_load_factor=value)

        for value in ("0.75", True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    HashTable(max_load_factor=value)

    def test_non_string_keys_are_rejected(self):
        table = HashTable()

        with self.assertRaises(TypeError):
            table.insert(1, "value")
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()
