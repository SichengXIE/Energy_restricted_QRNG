from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.special import erfc, gammaincc
from scipy.stats import chi2, poisson, norm


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
SUMMARY_PATH = FIG_DIR / "chapter3_simulation_summary.json"

WIDTH = 1500
HEIGHT = 920
BG = "#f4f7fb"
CARD_BG = "#ffffff"
FRAME = "#d7e1ec"
FG = "#1a1a1a"
GRID = "#d6d6d6"
BLUE = "#1f77b4"
ORANGE = "#ff7f0e"
GREEN = "#2ca02c"
RED = "#d62728"
PURPLE = "#6a3d9a"


def ensure_dirs(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)


def resolve_output_dir(output_dir: str | None) -> Path:
    return Path(output_dir) if output_dir else FIG_DIR


def prepare_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    try:
        draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=28, fill=CARD_BG, outline=FRAME, width=2)
    except AttributeError:
        draw.rectangle((24, 24, WIDTH - 24, HEIGHT - 24), fill=CARD_BG, outline=FRAME, width=2)
    return img, draw


def get_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_text(locale: str) -> dict[str, object]:
    if locale == "zh":
        return {
            "comp_left_title": "A 路压缩比与归一化熵余量",
            "comp_left_xlabel": "输出比特 / Hmin",
            "comp_left_ylabel": "(Hmin-OutputBits)/32",
            "comp_right_title": "A 路压缩比与平均偏置",
            "comp_right_xlabel": "输出比特 / Hmin",
            "comp_right_ylabel": "平均 |p-0.5|",
            "comp_notes": [
                "左图：基于保守最小熵预算得到的归一化熵余量。",
                "右图：按 1024-bit 输入块统计的行为级 Toeplitz 等效抽取器输出偏置。",
            ],
            "pvalue_title": "B 路统计测试电池 | NIST SP 800-22 子集与 Dieharder 同类测试",
            "pvalue_notes": [
                "当前工作区缺少官方 dieharder 二进制。",
                "因此热图使用相同行为级输出流上的 NIST 子集与 Dieharder 同类测试结果。",
            ],
            "row_labels": [
                "单比特",
                "分组频数",
                "游程",
                "序列-2",
                "近似熵",
                "累计和",
                "生日碰撞",
                "矩阵秩",
                "字节卡方",
                "配对卡方",
            ],
            "edc_title": "B 路在 EMI 注入下的熵赤字计数器时序",
            "edc_notes": [
                "EMI 注入后原始熵额度下降，异常检测后 A 路停止向 B 路继续播种。",
                "当熵赤字计数器越过阈值时，硬件清除 valid 并拉起 B_LINK_FAIL IRQ。",
            ],
            "trace_names": {
                "emi": "EMI 注入",
                "seed_valid": "Seed 有效",
                "output_valid": "输出有效",
                "edc": "EDC 数值",
                "irq": "B_LINK_FAIL 中断",
            },
        }
    return {
        "comp_left_title": "Track A compression ratio vs normalized entropy slack",
        "comp_left_xlabel": "Output bits / Hmin",
        "comp_left_ylabel": "(Hmin-OutputBits)/32",
        "comp_right_title": "Track A compression ratio vs mean bit bias",
        "comp_right_xlabel": "Output bits / Hmin",
        "comp_right_ylabel": "Mean |p-0.5|",
        "comp_notes": [
            "Left panel: normalized entropy slack derived from the conservative min-entropy budget.",
            "Right panel: empirical mean bit bias from the behavioral Toeplitz-equivalent extractor over 1024-bit blocks.",
        ],
        "pvalue_title": "Track B statistical battery | NIST SP 800-22 subset and dieharder-style tests",
        "pvalue_notes": [
            "The official dieharder binary is unavailable in the current workspace.",
            "The heatmap therefore uses a NIST subset and dieharder-style equivalent tests over the same behavioral output stream.",
        ],
        "row_labels": [
            "Monobit",
            "BlockFreq",
            "Runs",
            "Serial-2",
            "ApproxEnt",
            "CumSums",
            "Birthday",
            "Rank32",
            "ByteChi2",
            "PairChi2",
        ],
        "edc_title": "Track B entropy deficit counter timing under EMI injection",
        "edc_notes": [
            "EMI onset reduces raw entropy credit while Track A reseed stops after anomaly detection.",
            "When the entropy deficit counter crosses threshold, hardware clears valid and asserts B_LINK_FAIL IRQ.",
        ],
        "trace_names": {
            "emi": "EMI inject",
            "seed_valid": "Seed valid",
            "output_valid": "Output valid",
            "edc": "EDC value",
            "irq": "B_LINK_FAIL IRQ",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate chapter 3 simulation figures.")
    parser.add_argument("--locale", choices=("en", "zh"), default="en")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--with-svg", action="store_true", help="Also regenerate the legacy architecture SVG.")
    return parser.parse_args()


def draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, xlabel: str, ylabel: str) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline="#444444", width=2)
    draw.line((x0 + 80, y1 - 60, x1 - 24, y1 - 60), fill=FG, width=3)
    draw.line((x0 + 80, y1 - 60, x0 + 80, y0 + 30), fill=FG, width=3)
    draw.text((x0 + 80, y0 - 40), title, fill=FG, font=get_font(28))
    draw.text((x1 - 180, y1 - 48), xlabel, fill=FG, font=get_font(22))
    draw.text((x0 + 6, y0 + 36), ylabel, fill=FG, font=get_font(22))
    for i in range(1, 5):
        y = y0 + 30 + i * (y1 - y0 - 90) / 5
        x = x0 + 80 + i * (x1 - x0 - 104) / 5
        draw.line((x0 + 80, y, x1 - 24, y), fill=GRID, width=1)
        draw.line((x, y0 + 30, x, y1 - 60), fill=GRID, width=1)


def scale_points(xs: np.ndarray, ys: np.ndarray, box: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    left = x0 + 80
    right = x1 - 24
    top = y0 + 30
    bottom = y1 - 60
    xmin = float(xs.min())
    xmax = float(xs.max())
    ymin = float(ys.min())
    ymax = float(ys.max())
    if xmax == xmin:
        xmax = xmin + 1.0
    if ymax == ymin:
        ymax = ymin + 1.0
    pts = []
    for x, y in zip(xs, ys):
        px = left + (x - xmin) / (xmax - xmin) * (right - left)
        py = bottom - (y - ymin) / (ymax - ymin) * (bottom - top)
        pts.append((px, py))
    return pts


def stationary_markov_hmin(p01: float, p11: float) -> float:
    p10 = 1.0 - p11
    p0 = p10 / (p10 + p01)
    p1 = 1.0 - p0
    worst = max(1.0 - p01, p01, p11, 1.0 - p11, p0, p1)
    return -math.log2(worst)


def generate_markov_blocks(rng: np.random.Generator, n_blocks: int, n_bits: int, p01: float = 0.44, p11: float = 0.56) -> np.ndarray:
    bits = np.zeros((n_blocks, n_bits), dtype=np.uint8)
    initial = rng.random(n_blocks) > 0.5
    bits[:, 0] = initial.astype(np.uint8)
    for j in range(1, n_bits):
        prev = bits[:, j - 1]
        probs = np.where(prev == 1, p11, p01)
        bits[:, j] = (rng.random(n_blocks) < probs).astype(np.uint8)
    return bits


def random_dense_hash(blocks: np.ndarray, out_bits: int, rng: np.random.Generator) -> np.ndarray:
    matrix = rng.integers(0, 2, size=(out_bits, blocks.shape[1]), dtype=np.int16)
    products = blocks.astype(np.int16) @ matrix.T
    return (products & 1).astype(np.uint8)


def uniformity_metrics(bits: np.ndarray) -> tuple[float, float]:
    packed = np.packbits(bits, axis=1, bitorder="little")
    bytes_flat = packed.reshape(-1)
    counts = np.bincount(bytes_flat, minlength=256).astype(np.float64)
    probs = counts / counts.sum()
    tvd = 0.5 * np.sum(np.abs(probs - 1.0 / 256.0))
    bit_bias = float(np.abs(bits.mean() - 0.5))
    return float(tvd), bit_bias


def render_compression_uniformity(path: Path, ratios: np.ndarray, margin: np.ndarray, bias: np.ndarray, texts: dict[str, object]) -> None:
    img, draw = prepare_canvas()
    left_box = (70, 120, 720, 780)
    right_box = (790, 120, 1430, 780)
    draw_axes(
        draw,
        left_box,
        str(texts["comp_left_title"]),
        str(texts["comp_left_xlabel"]),
        str(texts["comp_left_ylabel"]),
    )
    draw_axes(
        draw,
        right_box,
        str(texts["comp_right_title"]),
        str(texts["comp_right_xlabel"]),
        str(texts["comp_right_ylabel"]),
    )

    tvd_pts = scale_points(ratios, margin, left_box)
    bias_pts = scale_points(ratios, bias, right_box)
    draw.line(tvd_pts, fill=BLUE, width=4)
    draw.line(bias_pts, fill=ORANGE, width=4)

    tick_font = get_font(18)
    for pts, ys, box in ((tvd_pts, margin, left_box), (bias_pts, bias, right_box)):
        for px, py in pts:
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=PURPLE)
        x0, y0, x1, y1 = box
        left = x0 + 80
        right = x1 - 24
        bottom = y1 - 60
        xmin = float(ratios.min())
        xmax = float(ratios.max())
        ymin = float(ys.min())
        ymax = float(ys.max())
        for x in ratios:
            px = left + (float(x) - xmin) / (xmax - xmin) * (right - left)
            draw.text((px - 16, bottom + 10), f"{x:.2f}", fill=FG, font=tick_font)
        for frac in np.linspace(0, 1, 6):
            yv = ymin + frac * (ymax - ymin)
            py = bottom - frac * (bottom - (y0 + 30))
            draw.text((x0 + 8, py - 10), f"{yv:.3f}", fill=FG, font=tick_font)

    note_y = 820
    note_font = get_font(20)
    for note in texts["comp_notes"]:
        draw.text((80, note_y), note, fill=FG, font=note_font)
        note_y += 24

    img.save(path)


def monobit_test(bits: np.ndarray) -> float:
    x = 2 * bits.astype(np.int16) - 1
    s_obs = abs(x.sum()) / math.sqrt(bits.size)
    return float(erfc(s_obs / math.sqrt(2.0)))


def block_frequency_test(bits: np.ndarray, block_size: int = 128) -> float:
    n_blocks = bits.size // block_size
    data = bits[: n_blocks * block_size].reshape(n_blocks, block_size)
    pis = data.mean(axis=1)
    chi = 4.0 * block_size * np.sum((pis - 0.5) ** 2)
    return float(gammaincc(n_blocks / 2.0, chi / 2.0))


def runs_test(bits: np.ndarray) -> float:
    pi = bits.mean()
    if abs(pi - 0.5) >= 2 / math.sqrt(bits.size):
        return 0.0
    v_obs = 1 + np.count_nonzero(bits[1:] != bits[:-1])
    num = abs(v_obs - 2.0 * bits.size * pi * (1.0 - pi))
    den = 2.0 * math.sqrt(2.0 * bits.size) * pi * (1.0 - pi)
    return float(erfc(num / den))


def serial2_test(bits: np.ndarray) -> float:
    circular = np.concatenate([bits, bits[:1]])
    patterns = circular[:-1] * 2 + circular[1:]
    counts = np.bincount(patterns, minlength=4)
    expected = np.full(4, patterns.size / 4.0)
    chi = np.sum((counts - expected) ** 2 / expected)
    return float(chi2.sf(chi, 3))


def approximate_entropy_test(bits: np.ndarray, m: int = 2) -> float:
    def phi(mm: int) -> float:
        extended = np.concatenate([bits, bits[: mm - 1]])
        patterns = np.zeros(bits.size, dtype=np.int32)
        for i in range(mm):
            patterns = (patterns << 1) | extended[i : i + bits.size]
        counts = np.bincount(patterns, minlength=2**mm).astype(np.float64)
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        return float(np.sum(probs * np.log(probs)))

    ap_en = phi(m) - phi(m + 1)
    chi = 2.0 * bits.size * (math.log(2) - ap_en)
    return float(gammaincc(2 ** (m - 1), chi / 2.0))


def cumulative_sums_test(bits: np.ndarray) -> float:
    x = 2 * bits.astype(np.int16) - 1
    s = np.cumsum(x)
    z = np.max(np.abs(s))
    z_norm = z / math.sqrt(bits.size)
    return float(2.0 * norm.sf(z_norm))


def birthday_collision_test(data: np.ndarray) -> float:
    words = np.frombuffer(data[: 2 * 4096], dtype=np.uint8)
    words = words.reshape(-1, 2)
    values = words[:, 0].astype(np.uint32) | (words[:, 1].astype(np.uint32) << 8)
    _, counts = np.unique(values, return_counts=True)
    collisions = int(np.sum(counts - 1))
    lam = values.size * (values.size - 1) / (2.0 * (2**16))
    cdf = poisson.cdf(collisions, lam)
    sf = poisson.sf(collisions - 1, lam)
    return float(min(1.0, 2.0 * min(cdf, sf)))


def gf2_rank(matrix: np.ndarray) -> int:
    mat = matrix.copy().astype(np.uint8)
    rows, cols = mat.shape
    rank = 0
    col = 0
    for r in range(rows):
        while col < cols and not mat[r:, col].any():
            col += 1
        if col >= cols:
            break
        pivot = r + np.argmax(mat[r:, col])
        if pivot != r:
            mat[[r, pivot]] = mat[[pivot, r]]
        pivot_row = mat[r].copy()
        for rr in range(rows):
            if rr != r and mat[rr, col]:
                mat[rr] ^= pivot_row
        rank += 1
        col += 1
    return rank


def matrix_rank_test(bits: np.ndarray) -> float:
    n_mats = min(32, bits.size // (32 * 32))
    mats = bits[: n_mats * 32 * 32].reshape(n_mats, 32, 32)
    ranks = np.array([gf2_rank(m) for m in mats])
    counts = np.array([
        np.count_nonzero(ranks == 32),
        np.count_nonzero(ranks == 31),
        np.count_nonzero(ranks <= 30),
    ], dtype=np.float64)
    expected = np.array([0.2888, 0.5776, 0.1336]) * n_mats
    chi = np.sum((counts - expected) ** 2 / expected)
    return float(chi2.sf(chi, 2))


def byte_distribution_test(data: np.ndarray) -> float:
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256).astype(np.float64)
    expected = np.full(256, counts.sum() / 256.0)
    chi = np.sum((counts - expected) ** 2 / expected)
    return float(chi2.sf(chi, 255))


def overlapping_pair_test(data: np.ndarray) -> float:
    byte_data = np.frombuffer(data, dtype=np.uint8)
    pairs = ((byte_data[:-1].astype(np.uint16) << 4) ^ (byte_data[1:] >> 4)).astype(np.uint16)
    counts = np.bincount(pairs, minlength=4096).astype(np.float64)
    expected = np.full(4096, counts.sum() / 4096.0)
    chi = np.sum((counts - expected) ** 2 / expected)
    return float(chi2.sf(chi, 4095))


def generate_b_raw_blocks(rng: np.random.Generator, n_blocks: int, block_bits: int = 512, n_channels: int = 8) -> np.ndarray:
    bits_per_channel = block_bits // n_channels
    outputs = np.zeros((n_blocks, block_bits), dtype=np.uint8)
    for blk in range(n_blocks):
        block = []
        shared = rng.normal(0.0, 0.010, bits_per_channel)
        for ch in range(n_channels):
            increments = rng.normal(0.0, 0.60 + 0.015 * ch, bits_per_channel) + shared
            phase = np.cumsum(increments)
            analog = np.cos(phase) + rng.normal(0.0, 0.04, bits_per_channel)
            raw = (analog > 0.0).astype(np.uint8)
            whitened = np.bitwise_xor(raw[1:], raw[:-1]).astype(np.uint8)
            padded = np.pad(whitened, (0, bits_per_channel - whitened.size), constant_values=0)
            block.append(padded)
        outputs[blk] = np.concatenate(block)
    return outputs


def shake256_expand(seed: bytes, raw_bits: np.ndarray, out_bytes: int = 64) -> bytes:
    raw_bytes = np.packbits(raw_bits, bitorder="little").tobytes()
    return hashlib.shake_256(seed + raw_bytes).digest(out_bytes)


def generate_b_output_stream(rng: np.random.Generator, windows: int = 4, bytes_per_window: int = 32768) -> list[bytes]:
    results = []
    seed = rng.bytes(32)
    for w in range(windows):
        chunks = []
        for block_idx in range(bytes_per_window // 64):
            if block_idx % 128 == 0:
                seed = hashlib.sha3_256(seed + rng.bytes(32)).digest()
            raw_block = generate_b_raw_blocks(rng, 1, 512)[0]
            mixed = shake256_expand(seed, raw_block, out_bytes=64)
            chunks.append(mixed)
        results.append(b"".join(chunks))
    return results


def render_pvalue_heatmap(path: Path, matrix: np.ndarray, row_labels: list[str], col_labels: list[str], texts: dict[str, object]) -> None:
    img, draw = prepare_canvas()
    draw.text((60, 34), str(texts["pvalue_title"]), fill=FG, font=get_font(30))
    x0, y0, x1, y1 = 230, 130, 1130, 760
    rows, cols = matrix.shape
    cell_w = (x1 - x0) / cols
    cell_h = (y1 - y0) / rows
    for i in range(rows):
        for j in range(cols):
            val = float(matrix[i, j])
            deviation = abs(val - 0.5) / 0.5
            if deviation < 0.4:
                color = (220 - int(60 * deviation), 245, 225 - int(30 * deviation))
            else:
                red = min(255, 220 + int(20 * deviation))
                green = max(180, 240 - int(90 * deviation))
                color = (red, green, 205)
            xx0 = x0 + j * cell_w
            yy0 = y0 + i * cell_h
            draw.rectangle((xx0, yy0, xx0 + cell_w, yy0 + cell_h), fill=color, outline="#666666")
            draw.text((xx0 + 28, yy0 + 18), f"{val:.3f}", fill=FG, font=get_font(18))
    for i, label in enumerate(row_labels):
        draw.text((70, y0 + i * cell_h + 18), label, fill=FG, font=get_font(20))
    for j, label in enumerate(col_labels):
        draw.text((x0 + j * cell_w + 38, y1 + 10), label, fill=FG, font=get_font(20))
    draw.text((1170, 170), "P-value", fill=FG, font=get_font(22))
    legend_y = 220
    for k, p in enumerate([0.01, 0.10, 0.50, 0.90, 0.99]):
        deviation = abs(p - 0.5) / 0.5
        if deviation < 0.4:
            color = (220 - int(60 * deviation), 245, 225 - int(30 * deviation))
        else:
            red = min(255, 220 + int(20 * deviation))
            green = max(180, 240 - int(90 * deviation))
            color = (red, green, 205)
        yy = legend_y + 46 * k
        draw.rectangle((1170, yy, 1210, yy + 30), fill=color, outline="#666666")
        draw.text((1225, yy + 4), f"{p:.2f}", fill=FG, font=get_font(18))
    note_y = 800
    for note in texts["pvalue_notes"]:
        draw.text((70, note_y), note, fill=FG, font=get_font(20))
        note_y += 24
    img.save(path)


def render_edc_waveform(path: Path, time: np.ndarray, traces: dict[str, np.ndarray], texts: dict[str, object]) -> None:
    img, draw = prepare_canvas()
    draw.text((60, 34), str(texts["edc_title"]), fill=FG, font=get_font(30))
    names = list(traces.keys())
    base_y = 150
    spacing = 110
    left = 160
    right = 1400
    top = 90
    bottom = 700
    draw.rectangle((left, top, right, bottom), outline="#555555", width=2)
    for tick in range(0, int(time.max()) + 1, 10):
        x = left + (tick - time.min()) / (time.max() - time.min()) * (right - left)
        draw.line((x, top, x, bottom), fill=GRID, width=1)
        draw.text((x - 10, bottom + 8), str(tick), fill=FG, font=get_font(16))

    for idx, name in enumerate(names):
        y_mid = base_y + idx * spacing
        draw.text((50, y_mid - 12), name, fill=FG, font=get_font(20))
        arr = traces[name]
        if arr.dtype.kind in "iu" and arr.max() > 1:
            y_min = float(arr.min())
            y_max = float(arr.max())
            y_range = max(1.0, y_max - y_min)
            pts = []
            for t, val in zip(time, arr):
                x = left + (t - time.min()) / (time.max() - time.min()) * (right - left)
                y = y_mid + 30 - (val - y_min) / y_range * 60
                pts.append((x, y))
            draw.line(pts, fill=PURPLE if "EDC" in name else BLUE, width=3)
            draw.text((right + 10, y_mid - 30), f"{int(y_max)}", fill=FG, font=get_font(16))
            draw.text((right + 10, y_mid + 20), f"{int(y_min)}", fill=FG, font=get_font(16))
        else:
            pts = []
            for t, val in zip(time, arr):
                x = left + (t - time.min()) / (time.max() - time.min()) * (right - left)
                y = y_mid + 20 - 40 * int(val)
                pts.append((x, y))
            for p0, p1 in zip(pts[:-1], pts[1:]):
                draw.line((p0[0], p0[1], p1[0], p0[1]), fill=RED if "valid" in name.lower() or "irq" in name.lower() else GREEN, width=3)
                draw.line((p1[0], p0[1], p1[0], p1[1]), fill=RED if "valid" in name.lower() or "irq" in name.lower() else GREEN, width=3)

    note_y = 760
    for note in texts["edc_notes"]:
        draw.text((70, note_y), note, fill=FG, font=get_font(20))
        note_y += 24
    img.save(path)


def create_architecture_svg(path: Path) -> None:
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="760" viewBox="0 0 1480 760">
<rect width="1480" height="760" fill="white"/>
<text x="40" y="46" font-size="30" font-family="Helvetica, Arial, sans-serif" fill="#1a1a1a">图 3-1 FPGA 内部数据流、隔离墙与 A→B Seed CDC 架构图</text>
<rect x="40" y="90" width="1380" height="620" rx="18" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<line x1="730" y1="120" x2="730" y2="680" stroke="#94a3b8" stroke-width="4" stroke-dasharray="14 10"/>
<text x="620" y="115" font-size="20" font-family="Helvetica, Arial, sans-serif" fill="#334155">物理隔离墙 / Floorplan Keep-Out</text>

<rect x="80" y="160" width="260" height="90" rx="14" fill="#dbeafe" stroke="#1d4ed8" stroke-width="2"/>
<text x="135" y="208" font-size="24" font-family="Helvetica, Arial, sans-serif">A 路原始采样 FIFO</text>
<rect x="80" y="300" width="260" height="110" rx="14" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
<text x="110" y="350" font-size="24" font-family="Helvetica, Arial, sans-serif">保守抽取器</text>
<text x="106" y="382" font-size="18" font-family="Helvetica, Arial, sans-serif">Toeplitz / AES-CMAC</text>
<rect x="80" y="470" width="260" height="90" rx="14" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
<text x="126" y="518" font-size="24" font-family="Helvetica, Arial, sans-serif">Cert Output FIFO</text>

<line x1="340" y1="205" x2="470" y2="205" stroke="#1d4ed8" stroke-width="4"/>
<line x1="340" y1="355" x2="470" y2="355" stroke="#0284c7" stroke-width="4"/>
<line x1="340" y1="515" x2="470" y2="515" stroke="#15803d" stroke-width="4"/>

<rect x="470" y="150" width="180" height="110" rx="14" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/>
<text x="500" y="198" font-size="22" font-family="Helvetica, Arial, sans-serif">健康测试 /</text>
<text x="500" y="226" font-size="22" font-family="Helvetica, Arial, sans-serif">元数据封装</text>
<rect x="470" y="320" width="180" height="90" rx="14" fill="#fae8ff" stroke="#a21caf" stroke-width="2"/>
<text x="510" y="370" font-size="22" font-family="Helvetica, Arial, sans-serif">A→B 监督器</text>
<rect x="470" y="460" width="180" height="120" rx="14" fill="#ede9fe" stroke="#6d28d9" stroke-width="2"/>
<text x="506" y="500" font-size="22" font-family="Helvetica, Arial, sans-serif">Seed CDC</text>
<text x="500" y="530" font-size="18" font-family="Helvetica, Arial, sans-serif">2-FF Sync +</text>
<text x="505" y="555" font-size="18" font-family="Helvetica, Arial, sans-serif">Pulse Stretch</text>

<rect x="820" y="160" width="260" height="90" rx="14" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
<text x="875" y="208" font-size="24" font-family="Helvetica, Arial, sans-serif">B 路原始采样 FIFO</text>
<rect x="820" y="300" width="260" height="110" rx="14" fill="#ffedd5" stroke="#ea580c" stroke-width="2"/>
<text x="845" y="350" font-size="24" font-family="Helvetica, Arial, sans-serif">激进抽取器 / DRBG</text>
<text x="855" y="382" font-size="18" font-family="Helvetica, Arial, sans-serif">512-bit @ 250 MHz</text>
<rect x="820" y="470" width="260" height="90" rx="14" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
<text x="872" y="518" font-size="24" font-family="Helvetica, Arial, sans-serif">Fast DMA FIFO</text>

<line x1="1080" y1="205" x2="1230" y2="205" stroke="#dc2626" stroke-width="4"/>
<line x1="1080" y1="355" x2="1230" y2="355" stroke="#ea580c" stroke-width="4"/>
<line x1="1080" y1="515" x2="1230" y2="515" stroke="#15803d" stroke-width="4"/>

<rect x="1230" y="150" width="150" height="110" rx="14" fill="#ecfccb" stroke="#65a30d" stroke-width="2"/>
<text x="1265" y="200" font-size="22" font-family="Helvetica, Arial, sans-serif">EDC</text>
<text x="1248" y="230" font-size="18" font-family="Helvetica, Arial, sans-serif">valid gate / IRQ</text>

<path d="M650 505 C720 505, 760 355, 820 355" fill="none" stroke="#6d28d9" stroke-width="4"/>
<polygon points="813,349 825,355 813,361" fill="#6d28d9"/>
<text x="670" y="472" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#6d28d9">Seed 注入 FIFO</text>
<path d="M650 365 C720 365, 760 250, 820 250" fill="none" stroke="#a21caf" stroke-width="3" stroke-dasharray="10 8"/>
<polygon points="813,244 825,250 813,256" fill="#a21caf"/>
<text x="652" y="334" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#a21caf">Histogram Bias / Threshold Update</text>

<text x="104" y="640" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#334155">A 路保守抽取器、健康测试器与 Seed CDC 位于左侧安全区域</text>
<text x="812" y="640" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#334155">B 路高速抽取、EDC 与 DMA 位于右侧高速区域</text>
</svg>""",
        encoding="utf-8",
    )


def render_heatmap_summary(streams: list[bytes], row_labels: list[str]) -> tuple[np.ndarray, list[str], list[str]]:
    col_labels = [f"W{i+1}" for i in range(len(streams))]
    matrix = np.zeros((len(row_labels), len(col_labels)))
    for j, stream in enumerate(streams):
        bytes_arr = np.frombuffer(stream, dtype=np.uint8)
        bits = np.unpackbits(bytes_arr, bitorder="little")
        pvals = [
            monobit_test(bits),
            block_frequency_test(bits),
            runs_test(bits),
            serial2_test(bits),
            approximate_entropy_test(bits),
            cumulative_sums_test(bits),
            birthday_collision_test(stream),
            matrix_rank_test(bits),
            byte_distribution_test(stream),
            overlapping_pair_test(stream),
        ]
        matrix[:, j] = np.clip(pvals, 1e-6, 1 - 1e-6)
    return matrix, row_labels, col_labels


def simulate_edc_waveform(texts: dict[str, object]) -> tuple[np.ndarray, dict[str, np.ndarray], dict]:
    time = np.arange(0, 121)
    emi = (time >= 72).astype(np.uint8)
    seed_valid = np.isin(time, [8, 40, 72]).astype(np.uint8)
    raw_credit = np.where(time < 72, 7, 1).astype(np.int32)
    output_debit = np.where(time < 94, 6, 0).astype(np.int32)
    threshold = 48
    edc = np.zeros_like(time, dtype=np.int32)
    valid = np.ones_like(time, dtype=np.uint8)
    irq = np.zeros_like(time, dtype=np.uint8)

    for i in range(1, time.size):
        credit = raw_credit[i] + (24 if seed_valid[i] else 0)
        edc[i] = max(0, edc[i - 1] + output_debit[i] - credit)
        if edc[i] >= threshold:
            valid[i:] = 0
            irq[i] = 1
            break

    trigger_cycle = int(np.argmax(irq))
    trace_names = texts["trace_names"]
    traces = {
        trace_names["emi"]: emi,
        trace_names["seed_valid"]: seed_valid,
        trace_names["output_valid"]: valid,
        trace_names["edc"]: edc,
        trace_names["irq"]: irq,
    }
    summary = {
        "threshold": threshold,
        "trigger_cycle": trigger_cycle,
        "trigger_time_ns_at_250mhz": trigger_cycle * 4,
        "max_edc_before_cutoff": int(edc[trigger_cycle]),
    }
    return time, traces, summary


def main() -> None:
    args = parse_args()
    fig_dir = resolve_output_dir(args.output_dir)
    summary_path = fig_dir / "chapter3_simulation_summary.json"
    texts = build_text(args.locale)
    ensure_dirs(fig_dir)
    rng = np.random.default_rng(20260414)

    # A-path compression/uniformity study
    n_blocks = 320
    raw_blocks = generate_markov_blocks(rng, n_blocks, 1024, p01=0.30, p11=0.70)
    hmin_per_bit = stationary_markov_hmin(0.30, 0.70)
    hmin_total = 1024 * hmin_per_bit
    output_bits = np.array([128, 192, 256, 320, 384, 448], dtype=np.int32)
    ratios = output_bits / hmin_total
    margin_vals = []
    bias_vals = []
    for out_bits in output_bits:
        out = random_dense_hash(raw_blocks, int(out_bits), rng)
        _tvd, bias = uniformity_metrics(out)
        margin_vals.append((hmin_total - int(out_bits)) / 32.0)
        bias_vals.append(bias)
    margin_vals = np.array(margin_vals)
    bias_vals = np.array(bias_vals)
    render_compression_uniformity(
        fig_dir / "chapter3_compression_uniformity.png",
        ratios,
        margin_vals,
        bias_vals,
        texts,
    )

    # B-path statistical battery
    streams = generate_b_output_stream(rng, windows=4, bytes_per_window=32768)
    p_matrix, row_labels, col_labels = render_heatmap_summary(streams, list(texts["row_labels"]))
    render_pvalue_heatmap(
        fig_dir / "chapter3_pvalue_heatmap.png",
        p_matrix,
        row_labels,
        col_labels,
        texts,
    )

    # EDC timing waveform
    time, traces, edc_summary = simulate_edc_waveform(texts)
    render_edc_waveform(
        fig_dir / "chapter3_edc_timing.png",
        time,
        traces,
        texts,
    )

    # Architecture figure
    if args.with_svg:
        create_architecture_svg(fig_dir / "chapter3_fpga_architecture.svg")

    summary = {
        "toolchain_note": {
            "iverilog_available": False,
            "dieharder_available": False,
            "method": "Python behavioral model with HDL-equivalent interfaces and local statistical battery",
        },
        "a_path_uniformity": {
            "hmin_per_bit": hmin_per_bit,
            "hmin_total_per_1024_block": hmin_total,
            "output_bits": output_bits.tolist(),
            "compression_ratio_output_over_hmin": ratios.tolist(),
            "normalized_entropy_slack": margin_vals.tolist(),
            "mean_bit_bias": bias_vals.tolist(),
            "recommended_operating_point_bits": 256,
            "recommended_operating_point_ratio": float(output_bits[2] / hmin_total),
        },
        "b_path_pvalues": {
            "row_labels": row_labels,
            "columns": col_labels,
            "matrix": p_matrix.tolist(),
            "min_pvalue": float(p_matrix.min()),
            "max_pvalue": float(p_matrix.max()),
            "mean_pvalue": float(p_matrix.mean()),
        },
        "edc_waveform": edc_summary,
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
