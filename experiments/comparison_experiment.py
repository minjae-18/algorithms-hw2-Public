"""Compare separate chaining with Python's built-in dictionary."""

import platform
import random
import sys
import time
from pathlib import Path

from src.hash_table import HashTable


ENTRY_COUNTS = (2_048, 8_192, 16_384)
BUILD_ROUNDS = 3
LOOKUP_ROUNDS = 5


def _keys(prefix: str, count: int, seed: int) -> list[str]:
    generator = random.Random(seed)
    return [f"{prefix}-{generator.getrandbits(128):032x}" for _ in range(count)]


def _build_chaining(keys: list[str]) -> tuple[HashTable, float]:
    table = HashTable()
    started = time.perf_counter()
    for index, key in enumerate(keys):
        table.insert(key, index)
    return table, time.perf_counter() - started


def _build_builtin_dict(keys: list[str]) -> tuple[dict[str, int], float]:
    table: dict[str, int] = {}
    started = time.perf_counter()
    for index, key in enumerate(keys):
        table[key] = index
    return table, time.perf_counter() - started


def _lookup_seconds_per_operation(
    table, keys: list[str], expected_values: list[int]
) -> float:
    elapsed = 0.0
    for _ in range(LOOKUP_ROUNDS):
        started = time.perf_counter()
        for index, key in enumerate(keys):
            if table.get(key) != expected_values[index]:
                raise RuntimeError(f"incorrect value returned for key {key}")
        elapsed += time.perf_counter() - started
    return elapsed / (LOOKUP_ROUNDS * len(keys))


def _miss_seconds_per_operation(table, missing_keys: list[str]) -> float:
    elapsed = 0.0
    for _ in range(LOOKUP_ROUNDS):
        started = time.perf_counter()
        for key in missing_keys:
            if table.get(key) is not None:
                raise RuntimeError(f"missing key unexpectedly found: {key}")
        elapsed += time.perf_counter() - started
    return elapsed / (LOOKUP_ROUNDS * len(missing_keys))


def _measure(entry_count: int, seed: int) -> tuple[float, ...]:
    keys = _keys("present", entry_count, seed)
    missing_keys = _keys("absent", entry_count, seed + 1)
    build_times = [0.0, 0.0]
    chaining_table = None
    builtin_table = None

    for _ in range(BUILD_ROUNDS):
        round_keys = [key.encode("utf-8").decode("utf-8") for key in keys]
        chaining_table, elapsed = _build_chaining(round_keys)
        build_times[0] += elapsed
        builtin_table, elapsed = _build_builtin_dict(round_keys)
        build_times[1] += elapsed

    if chaining_table is None or builtin_table is None:
        raise RuntimeError("benchmark did not build both tables")

    chaining_hit = _lookup_seconds_per_operation(
        chaining_table, round_keys, list(range(entry_count))
    )
    builtin_hit = _lookup_seconds_per_operation(
        builtin_table, round_keys, list(range(entry_count))
    )
    chaining_miss = _miss_seconds_per_operation(chaining_table, missing_keys)
    builtin_miss = _miss_seconds_per_operation(builtin_table, missing_keys)
    return (
        build_times[0] / (BUILD_ROUNDS * entry_count),
        build_times[1] / (BUILD_ROUNDS * entry_count),
        chaining_hit,
        builtin_hit,
        chaining_miss,
        builtin_miss,
    )


def _write_report(rows: list[tuple[int, tuple[float, ...]]], destination: Path) -> None:
    lines = [
        "# Hash-table implementation comparison",
        "",
        f"- Python: {sys.version.split()[0]}",
        f"- Platform: {platform.platform()}",
        f"- Build rounds: {BUILD_ROUNDS}; lookup rounds: {LOOKUP_ROUNDS}",
        "- Keys are deterministic random-looking strings; every result is checked.",
        "- Fresh string objects are used for each build round to avoid reusing cached string hashes.",
        "- The built-in dictionary is used only as the benchmark comparison target.",
        "- Times are measured on this runtime and machine; they are not portable guarantees.",
        "",
        "| Entries | Chaining insert (us/key) | dict insert (us/key) | Chaining hit (us/op) | dict hit (us/op) | Chaining miss (us/op) | dict miss (us/op) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry_count, measurements in rows:
        lines.append(
            f"| {entry_count:,} "
            f"| {measurements[0] * 1_000_000:.3f} "
            f"| {measurements[1] * 1_000_000:.3f} "
            f"| {measurements[2] * 1_000_000:.3f} "
            f"| {measurements[3] * 1_000_000:.3f} "
            f"| {measurements[4] * 1_000_000:.3f} "
            f"| {measurements[5] * 1_000_000:.3f} |"
        )
    lines.extend(
        [
            "",
            "The chaining table computes a deterministic Horner hash over each string "
            "and traverses linked lists; Python's dictionary uses its own optimized "
            "hash-table implementation. The benchmark does not call `hash()` itself. "
            "Timing differences include Python interpreter, allocator, and machine "
            "effects and should be interpreted as observations rather than algorithmic "
            "complexity proofs.",
            "",
        ]
    )
    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [
        (entry_count, _measure(entry_count, 7_202_611 + index))
        for index, entry_count in enumerate(ENTRY_COUNTS)
    ]
    report_path = Path(__file__).resolve().parent / "comparison_experiment.md"
    _write_report(rows, report_path)
    print(report_path)
    print(report_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
