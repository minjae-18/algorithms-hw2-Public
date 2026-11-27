"""Compare chaining and linear-probing search costs across load factors."""

import csv
import math
import random
import struct
import zlib
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


LOAD_FACTORS = tuple(index / 10 for index in range(1, 10))
TARGET_CAPACITY = 8192
SEED = 8_202_611


def _keys(prefix: str, count: int, seed: int) -> list[str]:
    generator = random.Random(seed)
    return [f"{prefix}-{generator.getrandbits(128):032x}" for _ in range(count)]


def _successful_search_cost(table, keys: list[str]) -> float:
    probes = 0
    for key in keys:
        if isinstance(table, HashTable):
            node = table._buckets[table._bucket_index(key)]
            while node is not None:
                probes += 1
                if node.key == key:
                    break
                node = node.next
            else:
                raise RuntimeError(f"inserted key was not found: {key}")
        else:
            index = table._bucket_index(key)
            for _ in range(table.capacity):
                probes += 1
                entry = table._slots[index]
                if entry is None:
                    raise RuntimeError(f"inserted key was not found: {key}")
                if entry.key == key:
                    break
                index = (index + 1) % table.capacity
            else:
                raise RuntimeError(f"inserted key was not found: {key}")
    return probes / len(keys)


def _unsuccessful_search_cost(table, missing_keys: list[str]) -> float:
    probes = 0
    for key in missing_keys:
        if isinstance(table, HashTable):
            node = table._buckets[table._bucket_index(key)]
            while node is not None:
                probes += 1
                node = node.next
        else:
            index = table._bucket_index(key)
            for _ in range(table.capacity):
                probes += 1
                if table._slots[index] is None:
                    break
                index = (index + 1) % table.capacity
            else:
                raise RuntimeError("an absent-key lookup scanned the full table")
    return probes / len(missing_keys)


def _measure(load_factor: float) -> tuple[float, ...]:
    entry_count = int(load_factor * TARGET_CAPACITY)
    keys = _keys("present", entry_count, SEED)
    missing_keys = _keys("absent", entry_count, SEED + 1)

    chaining = HashTable(max_load_factor=1.0, initial_capacity=TARGET_CAPACITY)
    linear = LinearProbingHashTable(
        max_load_factor=1.0, initial_capacity=TARGET_CAPACITY
    )
    for index, key in enumerate(keys):
        chaining.insert(key, index)
        linear.insert(key, index)

    if chaining.capacity != TARGET_CAPACITY or linear.capacity != TARGET_CAPACITY:
        raise RuntimeError("tables did not retain the target capacity")
    if chaining.size != entry_count or linear.size != entry_count:
        raise RuntimeError("tables did not store the same number of keys")

    actual_load_factor = entry_count / TARGET_CAPACITY
    return (
        actual_load_factor,
        _successful_search_cost(chaining, keys),
        1.0 + actual_load_factor / 2.0,
        _unsuccessful_search_cost(chaining, missing_keys),
        actual_load_factor,
        _successful_search_cost(linear, keys),
        0.5 * (1.0 + 1.0 / (1.0 - actual_load_factor)),
        _unsuccessful_search_cost(linear, missing_keys),
        0.5 * (1.0 + 1.0 / (1.0 - actual_load_factor) ** 2),
    )


def _write_markdown(rows: list[tuple[float, ...]], destination: Path) -> None:
    lines = [
        "# Linear probing and chaining search-cost experiment",
        "",
        f"- Capacity: {TARGET_CAPACITY:,}; same deterministic key set per load factor.",
        "- Cost is the average number of nodes or slots examined per lookup.",
        "- Successful and unsuccessful queries use separate, deterministic key sets.",
        "- Theory assumes uniform hashing for chaining and the standard approximation "
        "for linear probing; finite samples and primary clustering cause differences.",
        "- Theory: chaining hit = 1 + α/2; miss = α. Linear probing hit = "
        "0.5 × (1 + 1/(1-α)); miss = 0.5 × (1 + 1/(1-α)^2).",
        "- Graph legend: blue/green = chaining hit/miss; orange/red = linear-probing "
        "hit/miss; solid = measured, dashed = theory.",
        "",
        "| Load α | Chaining hit measured / theory | Chaining miss measured / theory | Linear hit measured / theory | Linear miss measured / theory |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row[0]:.1f} | {row[1]:.3f} / {row[2]:.3f} "
            f"| {row[3]:.3f} / {row[4]:.3f} "
            f"| {row[5]:.3f} / {row[6]:.3f} "
            f"| {row[7]:.3f} / {row[8]:.3f} |"
        )
    lines.append("")
    destination.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(rows: list[tuple[float, ...]], destination: Path) -> None:
    headers = (
        "load_factor",
        "chaining_success_measured",
        "chaining_success_theory",
        "chaining_unsuccessful_measured",
        "chaining_unsuccessful_theory",
        "linear_probing_success_measured",
        "linear_probing_success_theory",
        "linear_probing_unsuccessful_measured",
        "linear_probing_unsuccessful_theory",
    )
    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)


def _write_svg(rows: list[tuple[float, ...]], destination: Path) -> None:
    width, height = 1000, 620
    left, right, top, bottom = 85, 35, 45, 130
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_cost = max(max(row[1:]) for row in rows)
    y_max = max(2, math.ceil(max_cost))
    y_tick_step = max(1, math.ceil(y_max / 10))

    def point(load: float, cost: float) -> tuple[float, float]:
        return (
            left + load * plot_width,
            top + (y_max - cost) / y_max * plot_height,
        )

    series = (
        ("Chaining hit measured", 1, "#1565c0", "solid"),
        ("Chaining hit theory", 2, "#1565c0", "dash"),
        ("Chaining miss measured", 3, "#2e7d32", "solid"),
        ("Chaining miss theory", 4, "#2e7d32", "dash"),
        ("Linear hit measured", 5, "#ef6c00", "solid"),
        ("Linear hit theory", 6, "#ef6c00", "dash"),
        ("Linear miss measured", 7, "#c62828", "solid"),
        ("Linear miss theory", 8, "#c62828", "dash"),
    )
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif;fill:#222}.grid{stroke:#ddd}.axis{stroke:#444}.series{fill:none;stroke-width:2.2}</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="25" text-anchor="middle" font-size="18">Average search cost by load factor</text>',
    ]
    for tick in range(y_max + 1):
        y = point(0, tick)[1]
        pieces.append(
            f'<line class="grid" x1="{left}" y1="{y:.1f}" '
            f'x2="{width-right}" y2="{y:.1f}"/>'
        )
        if tick % y_tick_step == 0 or tick == y_max:
            pieces.append(
                f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" '
                f'font-size="11">{tick}</text>'
            )
    for tick in range(11):
        load = tick / 10
        x = point(load, 0)[0]
        pieces.append(
            f'<line class="grid" x1="{x:.1f}" y1="{top}" '
            f'x2="{x:.1f}" y2="{height-bottom}"/>'
        )
        pieces.append(
            f'<text x="{x:.1f}" y="{height-bottom+20}" '
            f'text-anchor="middle" font-size="11">{load:.1f}</text>'
        )
    pieces.extend(
        [
            f'<line class="axis" x1="{left}" y1="{height-bottom}" '
            f'x2="{width-right}" y2="{height-bottom}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" '
            f'x2="{left}" y2="{height-bottom}"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-18}" '
            'text-anchor="middle" font-size="14">Load factor α</text>',
            f'<text x="20" y="{top + plot_height/2:.1f}" '
            f'text-anchor="middle" font-size="14" '
            f'transform="rotate(-90 20 {top + plot_height/2:.1f})">'
            "Average examined nodes / slots</text>",
        ]
    )
    for label, value_index, color, style in series:
        points = [point(row[0], row[value_index]) for row in rows]
        coordinates = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dash = ' stroke-dasharray="6 4"' if style == "dash" else ""
        pieces.append(
            f'<polyline class="series" stroke="{color}"{dash} '
            f'points="{coordinates}"/>'
        )
        for x, y in points:
            pieces.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.7" fill="{color}"/>'
            )
    for index, (label, _, color, style) in enumerate(series):
        column = index % 2
        row_index = index // 2
        x = 120 + column * 440
        y = height - 90 + row_index * 17
        dash = ' stroke-dasharray="6 4"' if style == "dash" else ""
        pieces.append(
            f'<line x1="{x}" y1="{y}" x2="{x+25}" y2="{y}" '
            f'stroke="{color}" stroke-width="2.2"{dash}/>'
        )
        pieces.append(
            f'<text x="{x+32}" y="{y+4}" font-size="11">{label}</text>'
        )
    pieces.append("</svg>")
    destination.write_text("\n".join(pieces) + "\n", encoding="utf-8")


def _write_png(rows: list[tuple[float, ...]], destination: Path) -> None:
    width, height = 1000, 620
    left, right, top, bottom = 85, 35, 45, 130
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_cost = max(max(row[1:]) for row in rows)
    y_max = max(2, math.ceil(max_cost))
    y_tick_step = max(1, math.ceil(y_max / 10))
    pixels = bytearray(b"\xff" * (width * height * 3))

    def point(load: float, cost: float) -> tuple[int, int]:
        return (
            round(left + load * plot_width),
            round(top + (y_max - cost) / y_max * plot_height),
        )

    def put_pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset : offset + 3] = bytes(color)

    def draw_line(
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        dashed: bool = False,
    ) -> None:
        x0, y0 = start
        x1, y1 = end
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        step_x = 1 if x0 < x1 else -1
        step_y = 1 if y0 < y1 else -1
        error = dx + dy
        step = 0
        while True:
            if not dashed or step % 10 < 6:
                for offset_x in (0, 1):
                    for offset_y in (0, 1):
                        put_pixel(x0 + offset_x, y0 + offset_y, color)
            if (x0, y0) == (x1, y1):
                break
            twice_error = 2 * error
            if twice_error >= dy:
                error += dy
                x0 += step_x
            if twice_error <= dx:
                error += dx
                y0 += step_y
            step += 1

    grid = (220, 220, 220)
    axis = (68, 68, 68)
    for tick in range(y_max + 1):
        y = point(0, tick)[1]
        draw_line((left, y), (width - right, y), grid)
    for tick in range(11):
        x = point(tick / 10, 0)[0]
        draw_line((x, top), (x, height - bottom), grid)
    draw_line((left, top), (left, height - bottom), axis)
    draw_line((left, height - bottom), (width - right, height - bottom), axis)

    series = (
        (1, (21, 101, 192), False),
        (2, (21, 101, 192), True),
        (3, (46, 125, 50), False),
        (4, (46, 125, 50), True),
        (5, (239, 108, 0), False),
        (6, (239, 108, 0), True),
        (7, (198, 40, 40), False),
        (8, (198, 40, 40), True),
    )
    for value_index, color, dashed in series:
        points = [point(row[0], row[value_index]) for row in rows]
        for start, end in zip(points, points[1:]):
            draw_line(start, end, color, dashed)
        for x, y in points:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx * dx + dy * dy <= 4:
                        put_pixel(x + dx, y + dy, color)

    font = {
        "A": (2, 5, 7, 5, 5), "B": (6, 5, 6, 5, 6),
        "C": (3, 4, 4, 4, 3), "D": (6, 5, 5, 5, 6),
        "E": (7, 4, 6, 4, 7), "F": (7, 4, 6, 4, 4),
        "G": (3, 4, 5, 5, 3), "H": (5, 5, 7, 5, 5),
        "I": (7, 2, 2, 2, 7), "J": (1, 1, 1, 5, 2),
        "K": (5, 5, 6, 5, 5), "L": (4, 4, 4, 4, 7),
        "M": (5, 7, 7, 5, 5), "N": (5, 7, 7, 7, 5),
        "O": (2, 5, 5, 5, 2), "P": (6, 5, 6, 4, 4),
        "Q": (2, 5, 5, 7, 3), "R": (6, 5, 6, 5, 5),
        "S": (3, 4, 2, 1, 6), "T": (7, 2, 2, 2, 2),
        "U": (5, 5, 5, 5, 7), "V": (5, 5, 5, 5, 2),
        "W": (5, 5, 7, 7, 5), "X": (5, 5, 2, 5, 5),
        "Y": (5, 5, 2, 2, 2), "Z": (7, 1, 2, 4, 7),
        "0": (7, 5, 5, 5, 7), "1": (2, 6, 2, 2, 7),
        "2": (6, 1, 2, 4, 7), "3": (6, 1, 2, 1, 6),
        "4": (5, 5, 7, 1, 1), "5": (7, 4, 6, 1, 6),
        "6": (3, 4, 6, 5, 2), "7": (7, 1, 2, 2, 2),
        "8": (2, 5, 2, 5, 2), "9": (2, 5, 3, 1, 6),
        ".": (0, 0, 0, 0, 2), "-": (0, 0, 7, 0, 0),
        " ": (0, 0, 0, 0, 0),
    }

    def draw_text(text: str, x: int, y: int) -> None:
        scale = 2
        for character in text:
            glyph = font[character]
            for row_index, row_bits in enumerate(glyph):
                for column in range(3):
                    if row_bits & (1 << (2 - column)):
                        for dx in range(scale):
                            for dy in range(scale):
                                put_pixel(
                                    x + column * scale + dx,
                                    y + row_index * scale + dy,
                                    axis,
                                )
            x += 4 * scale

    for tick in range(y_max + 1):
        if tick % y_tick_step == 0 or tick == y_max:
            draw_text(str(tick), left - 32, point(0, tick)[1] - 5)
    title = "SEARCH COST BY LOAD FACTOR"
    draw_text(title, (width - len(title) * 8) // 2, 12)
    draw_text("COST", 18, 23)
    for tick in range(11):
        load = tick / 10
        x, y = point(load, 0)
        draw_text(f"{load:.1f}", x - 12, height - bottom + 7)
    draw_text("LOAD FACTOR", 435, height - bottom + 28)
    labels = (
        "CHAIN HIT MEASURED",
        "CHAIN HIT THEORY",
        "CHAIN MISS MEASURED",
        "CHAIN MISS THEORY",
        "LINEAR HIT MEASURED",
        "LINEAR HIT THEORY",
        "LINEAR MISS MEASURED",
        "LINEAR MISS THEORY",
    )
    for index, (label, (_, color, dashed)) in enumerate(zip(labels, series)):
        x = 120 + (index % 2) * 440
        y = height - 75 + (index // 2) * 16
        draw_line((x, y + 4), (x + 24, y + 4), color, dashed)
        draw_text(label, x + 32, y)

    def chunk(name: bytes, data: bytes) -> bytes:
        body = name + data
        return (
            struct.pack(">I", len(data))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    scanlines = b"".join(
        b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3]
        for y in range(height)
    )
    image = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines))
        + chunk(b"IEND", b"")
    )
    destination.write_bytes(image)


def main() -> None:
    rows = [_measure(load_factor) for load_factor in LOAD_FACTORS]
    output_dir = Path(__file__).resolve().parent
    csv_path = output_dir / "results.csv"
    markdown_path = output_dir / "probe_experiment.md"
    svg_path = output_dir / "probe_experiment.svg"
    png_path = output_dir / "probe_experiment.png"
    _write_csv(rows, csv_path)
    _write_markdown(rows, markdown_path)
    _write_svg(rows, svg_path)
    _write_png(rows, png_path)
    print(csv_path)
    print(markdown_path)
    print(svg_path)
    print(png_path)
    print(markdown_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
