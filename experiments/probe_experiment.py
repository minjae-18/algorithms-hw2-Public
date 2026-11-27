"""Measure separate-chaining probe counts across load-factor thresholds."""

import math
import random
import time
from pathlib import Path

from src.hash_table import HashTable


THRESHOLDS = (0.25, 0.5, 0.75, 0.9, 1.0, 1.5, 2.0, 3.0, 4.0)
TARGET_BUCKET_COUNT = 8192
INSERT_ROUNDS = 3
LOOKUP_ROUNDS = 3


def _keys(prefix: str, count: int, seed: int) -> list[str]:
    generator = random.Random(seed)
    return [f"{prefix}-{generator.getrandbits(128):032x}" for _ in range(count)]


def _build_table(keys: list[str], max_load_factor: float) -> tuple[HashTable, float]:
    started = time.perf_counter()
    table = HashTable(max_load_factor=max_load_factor)
    for index, key in enumerate(keys):
        table.insert(key, index)
    return table, time.perf_counter() - started


def _average_chain_lengths(table: HashTable) -> tuple[float, float]:
    total_nodes = 0
    nonempty_buckets = 0
    for head in table._buckets:
        chain_length = 0
        node = head
        while node is not None:
            chain_length += 1
            node = node.next
        total_nodes += chain_length
        if chain_length:
            nonempty_buckets += 1

    average_all_buckets = total_nodes / table.capacity
    average_nonempty_buckets = (
        total_nodes / nonempty_buckets if nonempty_buckets else 0.0
    )
    return average_all_buckets, average_nonempty_buckets


def _average_comparisons(table: HashTable, keys: list[str]) -> float:
    comparisons = 0
    for key in keys:
        node = table._buckets[table._bucket_index(key)]
        while node is not None:
            comparisons += 1
            if node.key == key:
                break
            node = node.next
        else:
            raise RuntimeError(f"inserted key was not found: {key}")
    return comparisons / len(keys)


def _average_miss_comparisons(table: HashTable, missing_keys: list[str]) -> float:
    comparisons = 0
    for key in missing_keys:
        node = table._buckets[table._bucket_index(key)]
        while node is not None:
            comparisons += 1
            node = node.next
    return comparisons / len(missing_keys)


def _average_lookup_seconds(
    table: HashTable, keys: list[str], expected_values: list[int]
) -> float:
    elapsed = 0.0
    for _ in range(LOOKUP_ROUNDS):
        started = time.perf_counter()
        for index, key in enumerate(keys):
            if table.get(key) != expected_values[index]:
                raise RuntimeError(f"lookup returned an incorrect value: {key}")
        elapsed += time.perf_counter() - started
    return elapsed / (LOOKUP_ROUNDS * len(keys))


def _average_miss_seconds(table: HashTable, keys: list[str]) -> float:
    elapsed = 0.0
    for _ in range(LOOKUP_ROUNDS):
        started = time.perf_counter()
        for key in keys:
            if table.get(key) is not None:
                raise RuntimeError(f"missing key unexpectedly exists: {key}")
        elapsed += time.perf_counter() - started
    return elapsed / (LOOKUP_ROUNDS * len(keys))


def _measure(threshold: float, keys: list[str], missing_keys: list[str]) -> list[float]:
    insertion_seconds = 0.0
    for _ in range(INSERT_ROUNDS):
        _, duration = _build_table(keys, threshold)
        insertion_seconds += duration
    table, _ = _build_table(keys, threshold)
    if table.capacity != TARGET_BUCKET_COUNT:
        raise RuntimeError(
            f"unexpected capacity for threshold {threshold}: {table.capacity}"
        )

    average_chain, average_nonempty_chain = _average_chain_lengths(table)
    actual_load_factor = table.size / table.capacity
    successful_comparisons = _average_comparisons(table, keys)
    unsuccessful_comparisons = _average_miss_comparisons(table, missing_keys)
    successful_lookup_seconds = _average_lookup_seconds(
        table, keys, list(range(len(keys)))
    )
    unsuccessful_lookup_seconds = _average_miss_seconds(table, missing_keys)

    return [
        threshold,
        actual_load_factor,
        average_chain,
        average_nonempty_chain,
        successful_comparisons,
        1.0 + actual_load_factor / 2.0,
        unsuccessful_comparisons,
        actual_load_factor,
        insertion_seconds / (INSERT_ROUNDS * len(keys)),
        successful_lookup_seconds,
        unsuccessful_lookup_seconds,
        float(len(keys)),
    ]


def _write_markdown(rows: list[list[float]], destination: Path) -> None:
    lines = [
        "# Hash-table load-factor experiment",
        "",
        f"- Target capacity: {TARGET_BUCKET_COUNT:,}; insertion rounds: {INSERT_ROUNDS}; lookup rounds: {LOOKUP_ROUNDS}",
        "- Average chain length includes empty buckets; nonempty-chain average is shown separately.",
        "- Theory uses the measured final load factor, not only the configured resize threshold.",
        "",
        "| Threshold | Entries | Actual α | Avg chain | Avg nonempty chain | Successful comparisons (measured / theory) | Unsuccessful comparisons (measured / theory) | Insert (µs/key) | Hit lookup (µs/op) | Miss lookup (µs/op) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row[0]:.2f} | {int(row[11]):,} | {row[1]:.3f} | {row[2]:.3f} | {row[3]:.3f} "
            f"| {row[4]:.3f} / {row[5]:.3f} | {row[6]:.3f} / {row[7]:.3f} "
            f"| {row[8] * 1_000_000:.3f} | {row[9] * 1_000_000:.3f} "
            f"| {row[10] * 1_000_000:.3f} |"
        )
    lines.extend(
        [
            "",
            "The theoretical comparison counts assume uniformly distributed keys and "
            "queries. Differences in the measured values reflect this table's "
            "deterministic string hash, finite sample, and query distribution; lookup "
            "times also include Python/runtime and machine noise.",
            "",
        ]
    )
    destination.write_text("\n".join(lines), encoding="utf-8")


def _write_svg(rows: list[list[float]], destination: Path) -> None:
    width, height = 900, 560
    left, right, top, bottom = 85, 35, 40, 100
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_load = 4.0
    max_comparisons = max(max(row[4], row[5], row[6], row[7]) for row in rows)
    y_max = max(2, math.ceil(max_comparisons))

    def point(load: float, comparisons: float) -> tuple[float, float]:
        x = left + load / max_load * plot_width
        y = top + (y_max - comparisons) / y_max * plot_height
        return x, y

    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif;fill:#222}.grid{stroke:#ddd}.axis{stroke:#444}.series{fill:none;stroke-width:2.5}</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="24" text-anchor="middle" font-size="18">Average chain comparisons by load factor</text>',
    ]

    for tick in range(y_max + 1):
        y = point(0, tick)[1]
        pieces.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}"/>')
        pieces.append(f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-size="12">{tick}</text>')
    for tick in range(5):
        x = left + tick / max_load * plot_width
        pieces.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}"/>')
        pieces.append(f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" font-size="12">{tick}</text>')
    pieces.extend(
        [
            f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-18}" text-anchor="middle" font-size="14">Actual load factor α</text>',
            f'<text x="20" y="{top + plot_height/2:.1f}" text-anchor="middle" font-size="14" transform="rotate(-90 20 {top + plot_height/2:.1f})">Average node comparisons</text>',
        ]
    )

    series = (
        ("Successful (measured)", 1, 4, "#1565c0", "solid"),
        ("Successful (theory)", 1, 5, "#1565c0", "dash"),
        ("Unsuccessful (measured)", 1, 6, "#c62828", "solid"),
        ("Unsuccessful (theory)", 1, 7, "#c62828", "dash"),
    )
    for label, load_index, comparison_index, color, style in series:
        points = [
            point(row[load_index], row[comparison_index])
            for row in rows
        ]
        points_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dash = ' stroke-dasharray="7 5"' if style == "dash" else ""
        pieces.append(
            f'<polyline class="series" stroke="{color}"{dash} points="{points_text}"/>'
        )
        for x, y in points:
            pieces.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')

    legend_y = height - 58
    legend_positions = (110, 340, 540, 740)
    for index, (label, _, _, color, style) in enumerate(series):
        x = legend_positions[index]
        dash = ' stroke-dasharray="7 5"' if style == "dash" else ""
        pieces.append(f'<line x1="{x}" y1="{legend_y}" x2="{x+25}" y2="{legend_y}" stroke="{color}" stroke-width="2.5"{dash}/>')
        pieces.append(f'<text x="{x+31}" y="{legend_y+4}" font-size="11">{label}</text>')
    pieces.append("</svg>")
    destination.write_text("\n".join(pieces) + "\n", encoding="utf-8")


def main() -> None:
    rows = []
    for index, threshold in enumerate(THRESHOLDS):
        entry_count = int(threshold * TARGET_BUCKET_COUNT)
        keys = _keys("key", entry_count, 6_202_611 + index)
        missing_keys = _keys("absent", entry_count, 8_202_611 + index)
        rows.append(_measure(threshold, keys, missing_keys))
    output_dir = Path(__file__).resolve().parent
    markdown_path = output_dir / "probe_experiment.md"
    svg_path = output_dir / "probe_experiment.svg"
    _write_markdown(rows, markdown_path)
    _write_svg(rows, svg_path)
    print(markdown_path)
    print(svg_path)
    print(markdown_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
