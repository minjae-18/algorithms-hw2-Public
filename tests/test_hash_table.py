import unittest

from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


TABLE_TYPES = (HashTable, LinearProbingHashTable)


class HashTableTests(unittest.TestCase):
    def test_empty_table_returns_none(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type()
                self.assertEqual(table.capacity, 8)
                self.assertEqual(table.size, 0)
                self.assertIsNone(table.get("missing"))

    def test_initial_capacity_must_be_a_positive_integer(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                self.assertEqual(table_type(initial_capacity=16).capacity, 16)
                for value in (0, -1):
                    with self.assertRaises(ValueError):
                        table_type(initial_capacity=value)
                for value in (1.5, "8", True):
                    with self.assertRaises(TypeError):
                        table_type(initial_capacity=value)

    def test_colliding_keys_can_be_inserted_and_retrieved(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type()
                keys = ["a", "i", "q"]

                for index, key in enumerate(keys):
                    self.assertTrue(table.insert(key, index))

                self.assertEqual([table.get(key) for key in keys], [0, 1, 2])
                self.assertEqual(table.size, 3)

    def test_linear_probing_wraps_and_resizes_when_full(self):
        table = LinearProbingHashTable(max_load_factor=1.0)
        keys = ["g", "o", "w", "G", "O", "W", "_", "/"]

        for index, key in enumerate(keys):
            self.assertTrue(table.insert(key, index))

        self.assertEqual(table.capacity, 8)
        self.assertEqual(table.size, 8)
        self.assertEqual([table.get(key) for key in keys], list(range(8)))
        self.assertIsNone(table.get("not-present"))
        self.assertFalse(table.insert(keys[0], -1))

        self.assertTrue(table.insert("next", 8))

        self.assertEqual(table.capacity, 16)
        self.assertEqual(table.size, 9)
        self.assertEqual([table.get(key) for key in keys], list(range(8)))
        self.assertEqual(table.get("next"), 8)

    def test_duplicate_key_does_not_replace_value_or_increase_size(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type()
                self.assertTrue(table.insert("key", "original"))
                self.assertFalse(table.insert("key", "replacement"))
                self.assertEqual(table.get("key"), "original")
                self.assertEqual(table.size, 1)

    def test_table_resizes_after_load_exceeds_three_quarters(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type()
                for index in range(6):
                    self.assertTrue(table.insert(f"key-{index}", index))
                self.assertEqual(table.capacity, 8)
                self.assertTrue(table.insert("key-6", 6))
                self.assertEqual(table.capacity, 16)
                self.assertEqual(table.size, 7)
                for index in range(7):
                    self.assertEqual(table.get(f"key-{index}"), index)

    def test_table_uses_configured_maximum_load_factor(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type(max_load_factor=0.5)
                for index in range(5):
                    self.assertTrue(table.insert(f"key-{index}", index))
                self.assertEqual(table.capacity, 16)
                self.assertEqual(table.size, 5)
                for index in range(5):
                    self.assertEqual(table.get(f"key-{index}"), index)

    def test_maximum_load_factor_must_be_finite_and_positive(self):
        for table_type in TABLE_TYPES:
            for value in (0, -0.5, float("inf"), float("nan")):
                with self.subTest(table=table_type.__name__, value=value):
                    with self.assertRaises(ValueError):
                        table_type(max_load_factor=value)
            for value in ("0.75", True):
                with self.subTest(table=table_type.__name__, value=value):
                    with self.assertRaises(TypeError):
                        table_type(max_load_factor=value)

    def test_non_string_keys_are_rejected(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table=table_type.__name__):
                table = table_type()
                with self.assertRaises(TypeError):
                    table.insert(1, "value")
                with self.assertRaises(TypeError):
                    table.get(1)


if __name__ == "__main__":
    unittest.main()
