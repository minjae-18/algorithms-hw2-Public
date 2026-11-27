import ast
import unittest
from pathlib import Path


class ImplementationConstraintTests(unittest.TestCase):
    def test_core_sources_avoid_builtin_dict_set_and_hash(self):
        source_root = Path(__file__).resolve().parents[1] / "src"
        forbidden_names = {"dict", "set", "hash"}
        source_files = ("base62.py", "hash_table.py", "shortener.py")

        for filename in source_files:
            with self.subTest(filename=filename):
                source_path = source_root / filename
                tree = ast.parse(source_path.read_text(encoding="utf-8"))
                builtins_modules = {"builtins"}
                builtin_aliases = set(forbidden_names)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        builtins_modules.update(
                            alias.asname or alias.name
                            for alias in node.names
                            if alias.name == "builtins"
                        )
                    elif isinstance(node, ast.ImportFrom) and node.module == "builtins":
                        builtin_aliases.update(
                            alias.asname or alias.name
                            for alias in node.names
                            if alias.name in forbidden_names
                        )

                violations = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)):
                        violations.append(
                            f"line {node.lineno}: {type(node).__name__}"
                        )
                    elif isinstance(node, ast.Call):
                        function = node.func
                        if isinstance(function, ast.Name) and function.id in builtin_aliases:
                            violations.append(
                                f"line {node.lineno}: call to {function.id}"
                            )
                        elif (
                            isinstance(function, ast.Attribute)
                            and isinstance(function.value, ast.Name)
                            and function.value.id in builtins_modules
                            and function.attr in forbidden_names
                        ):
                            violations.append(
                                f"line {node.lineno}: call to builtins.{function.attr}"
                            )

                self.assertEqual(violations, [], f"{source_path}: {violations}")


if __name__ == "__main__":
    unittest.main()
