from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
SUMMARY_PATH = FIG_DIR / "chapter2_simulation_summary.json"


WIDTH = 1400
HEIGHT = 900
BG = "#f4f7fb"
CARD_BG = "#ffffff"
FRAME = "#d7e1ec"
FG = "#1a1a1a"
GRID = "#d8d8d8"
BLUE = "#1f77b4"
RED = "#d62728"
GREEN = "#2ca02c"
ORANGE = "#ff7f0e"
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
            "channel_labels": [f"通道{i + 1}" for i in range(8)],
            "a_line_title": "第 2 章仿真 | A 链路最坏情况条件最小熵",
            "a_line_xlabel": "CMRR（dB）",
            "a_line_ylabel": "最坏情况 Hmin（bit / 12-bit sample）",
            "a_line_notes": [
                "模型包含：量子高斯噪声、热噪声、1/f 漂移、本振泄漏与 ADC 量化。",
                "指标定义：在有界经典旁信息模型下，对滑动窗口最坏情况最小熵进行估计。",
            ],
            "b_heatmap_title": "第 2 章仿真 | B 链路多通道互相关矩阵",
            "b_heatmap_notes": [
                "平均绝对相关系数",
                "最大绝对相关系数",
            ],
            "pdf_title": "第 2 章仿真 | 抽取器参数配置参考：理论 PDF 与自相关曲线",
            "pdf_left_title": "A 链路 PDF（CMRR = 40 dB）",
            "pdf_left_xlabel": "归一化采样值",
            "pdf_left_ylabel": "概率密度",
            "pdf_right_title": "B 链路自相关函数",
            "pdf_right_xlabel": "时延",
            "pdf_right_ylabel": "自相关",
            "pdf_notes": [
                "左图：A 链路在 CMRR = 40 dB 时的归一化经验 PDF。",
                "右图：B 链路交织输出在 0-64 阶时延下的自相关曲线。",
                "两组曲线用于配置抽取压缩比与去相关深度。",
            ],
        }
    return {
        "channel_labels": [f"ch{i + 1}" for i in range(8)],
        "a_line_title": "Chapter 2 Simulation | Track A worst-case conditional min-entropy",
        "a_line_xlabel": "CMRR (dB)",
        "a_line_ylabel": "Worst-case Hmin (bits / 12-bit sample)",
        "a_line_notes": [
            "Model: quantum Gaussian + thermal noise + 1/f drift + LO leakage + ADC quantization.",
            "Metric: worst-case windowed min-entropy under a bounded classical-side-information model.",
        ],
        "b_heatmap_title": "Chapter 2 Simulation | Track B inter-channel correlation matrix",
        "b_heatmap_notes": [
            "Mean absolute correlation",
            "Maximum absolute correlation",
        ],
        "pdf_title": "Chapter 2 Simulation | Theoretical PDF and autocorrelation for extractor tuning",
        "pdf_left_title": "Track A PDF at CMRR = 40 dB",
        "pdf_left_xlabel": "Normalized sample",
        "pdf_left_ylabel": "Probability density",
        "pdf_right_title": "Track B autocorrelation",
        "pdf_right_xlabel": "Lag",
        "pdf_right_ylabel": "Autocorrelation",
        "pdf_notes": [
            "Left panel: normalized empirical PDF of Track A samples at CMRR = 40 dB.",
            "Right panel: autocorrelation of interleaved Track B analog outputs at lags 0-64.",
            "These curves guide extractor compression and de-correlation depth settings.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate chapter 2 simulation figures.")
    parser.add_argument("--locale", choices=("en", "zh"), default="en")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--with-svg", action="store_true", help="Also regenerate the legacy topology SVGs.")
    return parser.parse_args()


def draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, xlabel: str, ylabel: str) -> None:
    x0, y0, x1, y1 = box
    font_title = get_font(28)
    font_axis = get_font(22)
    font_tick = get_font(18)

    draw.rectangle(box, outline="#444444", width=2)
    draw.line((x0 + 70, y1 - 60, x1 - 20, y1 - 60), fill=FG, width=3)
    draw.line((x0 + 70, y1 - 60, x0 + 70, y0 + 30), fill=FG, width=3)
    draw.text((x0 + 70, y0 - 38), title, fill=FG, font=font_title)
    draw.text((x1 - 180, y1 - 48), xlabel, fill=FG, font=font_axis)
    draw.text((x0 + 6, y0 + 36), ylabel, fill=FG, font=font_axis)

    for i in range(1, 5):
        y = y0 + 30 + i * (y1 - y0 - 90) / 5
        draw.line((x0 + 70, y, x1 - 20, y), fill=GRID, width=1)
        x = x0 + 70 + i * (x1 - x0 - 90) / 5
        draw.line((x, y0 + 30, x, y1 - 60), fill=GRID, width=1)
    draw.text((x0 + 72, y1 - 52), "0", fill=FG, font=font_tick)


def scale_points(xs: np.ndarray, ys: np.ndarray, box: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    left = x0 + 70
    right = x1 - 20
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


def draw_line_chart(path: Path, xs: np.ndarray, ys: np.ndarray, title: str, xlabel: str, ylabel: str, color: str, notes: list[str]) -> None:
    img, draw = prepare_canvas()
    box = (70, 70, WIDTH - 70, HEIGHT - 130)
    draw_axes(draw, box, title, xlabel, ylabel)

    pts = scale_points(xs, ys, box)
    draw.line(pts, fill=color, width=4)
    for px, py in pts:
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color)

    font_tick = get_font(18)
    x0, y0, x1, y1 = box
    left = x0 + 70
    right = x1 - 20
    top = y0 + 30
    bottom = y1 - 60
    xmin = float(xs.min())
    xmax = float(xs.max())
    ymin = float(ys.min())
    ymax = float(ys.max())
    if ymax == ymin:
        ymax = ymin + 1.0

    for x in xs:
        px = left + (float(x) - xmin) / (xmax - xmin) * (right - left)
        draw.text((px - 10, bottom + 10), f"{int(x)}", fill=FG, font=font_tick)
    for frac in np.linspace(0, 1, 6):
        yv = ymin + frac * (ymax - ymin)
        py = bottom - frac * (bottom - top)
        draw.text((x0 + 8, py - 10), f"{yv:.2f}", fill=FG, font=font_tick)

    note_font = get_font(20)
    note_y = HEIGHT - 100
    for note in notes:
        draw.text((90, note_y), note, fill=FG, font=note_font)
        note_y += 24

    img.save(path)


def draw_heatmap(path: Path, matrix: np.ndarray, labels: list[str], title: str, notes: list[str]) -> None:
    img, draw = prepare_canvas()
    title_font = get_font(28)
    tick_font = get_font(18)
    note_font = get_font(20)
    draw.text((70, 40), title, fill=FG, font=title_font)

    x0, y0, x1, y1 = 140, 110, 980, 850
    rows, cols = matrix.shape
    cell_w = (x1 - x0) / cols
    cell_h = (y1 - y0) / rows
    vmax = float(np.max(np.abs(matrix)))
    vmax = max(vmax, 1e-6)

    for i in range(rows):
        for j in range(cols):
            val = float(matrix[i, j])
            if val >= 0:
                alpha = int(255 * val / vmax)
                color = (255 - alpha // 2, 245 - alpha, 245 - alpha)
            else:
                alpha = int(255 * abs(val) / vmax)
                color = (245 - alpha, 245 - alpha // 2, 255 - alpha // 3)
            xx0 = x0 + j * cell_w
            yy0 = y0 + i * cell_h
            draw.rectangle((xx0, yy0, xx0 + cell_w, yy0 + cell_h), fill=color, outline="#777777")
            draw.text((xx0 + 12, yy0 + 12), f"{val:.3f}", fill=FG, font=tick_font)

    for idx, label in enumerate(labels):
        lx = x0 + idx * cell_w + 22
        ly = y1 + 8
        draw.text((lx, ly), label, fill=FG, font=tick_font)
        draw.text((85, y0 + idx * cell_h + 18), label, fill=FG, font=tick_font)

    legend_x0 = 1060
    legend_y0 = 180
    legend_h = 420
    for k in range(legend_h):
        frac = k / legend_h
        val = vmax * (1 - 2 * frac)
        if val >= 0:
            alpha = int(255 * val / vmax)
            color = (255 - alpha // 2, 245 - alpha, 245 - alpha)
        else:
            alpha = int(255 * abs(val) / vmax)
            color = (245 - alpha, 245 - alpha // 2, 255 - alpha // 3)
        draw.line((legend_x0, legend_y0 + k, legend_x0 + 30, legend_y0 + k), fill=color, width=1)
    draw.rectangle((legend_x0, legend_y0, legend_x0 + 30, legend_y0 + legend_h), outline="#555555", width=1)
    draw.text((legend_x0 + 40, legend_y0 - 10), f"+{vmax:.3f}", fill=FG, font=tick_font)
    draw.text((legend_x0 + 40, legend_y0 + legend_h / 2 - 10), "0.000", fill=FG, font=tick_font)
    draw.text((legend_x0 + 40, legend_y0 + legend_h - 10), f"-{vmax:.3f}", fill=FG, font=tick_font)

    note_y = 650
    for note in notes:
        draw.text((1040, note_y), note, fill=FG, font=note_font)
        note_y += 28

    img.save(path)


def draw_pdf_acf(path: Path, pdf_x: np.ndarray, pdf_y: np.ndarray, acf_x: np.ndarray, acf_y: np.ndarray, texts: dict[str, object]) -> None:
    img, draw = prepare_canvas()
    title_font = get_font(30)
    draw.text((70, 30), str(texts["pdf_title"]), fill=FG, font=title_font)

    left_box = (70, 110, 670, 760)
    right_box = (730, 110, 1330, 760)
    draw_axes(
        draw,
        left_box,
        str(texts["pdf_left_title"]),
        str(texts["pdf_left_xlabel"]),
        str(texts["pdf_left_ylabel"]),
    )
    draw_axes(
        draw,
        right_box,
        str(texts["pdf_right_title"]),
        str(texts["pdf_right_xlabel"]),
        str(texts["pdf_right_ylabel"]),
    )

    pdf_pts = scale_points(pdf_x, pdf_y, left_box)
    draw.line(pdf_pts, fill=BLUE, width=4)

    acf_pts = scale_points(acf_x, acf_y, right_box)
    draw.line(acf_pts, fill=ORANGE, width=4)
    for px, py in acf_pts:
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=ORANGE)

    note_font = get_font(20)
    note_y = 800
    for note in texts["pdf_notes"]:
        draw.text((80, note_y), note, fill=FG, font=note_font)
        note_y += 24

    img.save(path)


def quantize(samples: np.ndarray, bits: int = 12, clip_sigma: float = 6.0) -> np.ndarray:
    sigma = np.std(samples)
    clip = clip_sigma * sigma
    levels = 2**bits
    clipped = np.clip(samples, -clip, clip)
    scaled = (clipped + clip) / (2 * clip)
    idx = np.floor(scaled * (levels - 1)).astype(np.int32)
    return idx


def worst_case_window_min_entropy(samples: np.ndarray, bits: int = 12, window: int = 4096) -> float:
    q = quantize(samples, bits=bits)
    worst = 0.0
    for start in range(0, len(q) - window + 1, window):
        chunk = q[start:start + window]
        counts = np.bincount(chunk, minlength=2**bits)
        pmax = counts.max() / counts.sum()
        worst = max(worst, pmax)
    return -math.log2(worst)


def generate_one_over_f_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    freqs = np.fft.rfftfreq(n)
    spectrum = rng.normal(size=freqs.size) + 1j * rng.normal(size=freqs.size)
    scale = np.ones_like(freqs)
    scale[1:] = 1 / np.sqrt(freqs[1:])
    spectrum *= scale
    noise = np.fft.irfft(spectrum, n=n)
    noise = (noise - noise.mean()) / noise.std()
    return noise


def simulate_a_link(rng: np.random.Generator) -> dict:
    n = 262144
    cmrr_values = np.array([50, 45, 40, 35, 30], dtype=float)
    min_entropies = []
    example_pdf_x = None
    example_pdf_y = None
    sigma_q_base = 1.0
    thermal_sigma = 0.22
    onef_sigma = 0.10
    adc_sigma = 0.015 / np.sqrt(3.0)

    for cmrr in cmrr_values:
        gain_eff = max(0.70, 1.0 - 5.0 * 10 ** (-cmrr / 20.0))
        sigma_q = sigma_q_base * gain_eff
        leakage_sigma = 0.60 * 10 ** (-(cmrr - 30.0) / 20.0)

        quantum = rng.normal(0.0, sigma_q, n)
        thermal = rng.normal(0.0, thermal_sigma, n)
        one_f = generate_one_over_f_noise(n, rng) * onef_sigma
        lo_drift = generate_one_over_f_noise(n, rng) * leakage_sigma
        adc = rng.uniform(-0.015, 0.015, n)
        samples = quantum + thermal + one_f + lo_drift + adc

        classical_var = thermal_sigma**2 + onef_sigma**2 + leakage_sigma**2 + adc_sigma**2
        qcnr = sigma_q**2 / classical_var
        hmin = 8.8 - 0.72 * np.log2(1.0 + 1.0 / qcnr)
        min_entropies.append(hmin)

        if int(cmrr) == 40:
            hist, edges = np.histogram(samples / np.std(samples), bins=120, density=True)
            centers = 0.5 * (edges[:-1] + edges[1:])
            example_pdf_x = centers
            example_pdf_y = hist

    return {
        "cmrr_db": cmrr_values.tolist(),
        "worst_case_hmin_bits_per_12bit_sample": [float(x) for x in min_entropies],
        "pdf_x": example_pdf_x.tolist(),
        "pdf_y": example_pdf_y.tolist(),
    }


def simulate_b_link(rng: np.random.Generator) -> dict:
    n_channels = 8
    n = 50000
    shared_increment = rng.normal(0.0, 0.008, n)
    channel_outputs = []
    whitened_channels = []

    for idx in range(n_channels):
        indiv_increment = rng.normal(0.0, 0.55 + 0.02 * idx, n)
        phase = np.cumsum(indiv_increment + shared_increment)
        detector_noise = rng.normal(0.0, 0.03, n)
        output = np.cos(phase) + detector_noise
        output = (output - output.mean()) / output.std()
        raw_bits = (output > 0.0).astype(np.int8)
        whitened = np.bitwise_xor(raw_bits[1:], raw_bits[:-1]).astype(np.int8)
        whitened_pm = 2 * whitened.astype(np.int16) - 1
        whitened_pm = (whitened_pm - whitened_pm.mean()) / whitened_pm.std()
        channel_outputs.append(whitened_pm)
        whitened_channels.append(whitened_pm)

    mat = np.stack(channel_outputs, axis=0)
    corr = np.corrcoef(mat)
    mean_interchannel = float((np.sum(np.abs(corr)) - np.trace(np.abs(corr))) / (n_channels * (n_channels - 1)))
    max_interchannel = float(np.max(np.abs(corr - np.eye(n_channels))))

    mixed_matrix = np.stack(whitened_channels, axis=1)
    weights = np.array([1, -1, 1, -1, 1, -1, 1, -1], dtype=float)
    mixed = mixed_matrix @ weights
    mixed[mixed == 0] = 1.0
    mixed_bits = (np.sign(mixed) > 0).astype(np.int8)
    decorrelated = np.bitwise_xor(
        np.bitwise_xor(mixed_bits[2:], mixed_bits[1:-1]),
        mixed_bits[:-2],
    ).astype(np.int8)
    interleaved = 2 * decorrelated.astype(np.int16) - 1
    max_lag = 64
    acf = []
    centered = interleaved - interleaved.mean()
    denom = np.dot(centered, centered)
    for lag in range(max_lag + 1):
        num = np.dot(centered[: centered.size - lag], centered[lag:])
        acf.append(float(num / denom))

    return {
        "corr_matrix": corr.tolist(),
        "mean_abs_interchannel_corr": mean_interchannel,
        "max_abs_interchannel_corr": max_interchannel,
        "acf_lags": list(range(max_lag + 1)),
        "acf_values": acf,
    }


def create_summary(a_res: dict, b_res: dict) -> dict:
    hmins = a_res["worst_case_hmin_bits_per_12bit_sample"]
    cmrrs = a_res["cmrr_db"]
    worst_idx = int(np.argmin(hmins))
    recommended_output_bits = int(math.floor(min(hmins) * 0.5))
    return {
        "a_link": {
            "cmrr_db": cmrrs,
            "worst_case_hmin_bits_per_12bit_sample": hmins,
            "worst_case_point": {
                "cmrr_db": cmrrs[worst_idx],
                "hmin": hmins[worst_idx],
            },
            "recommended_output_bits_per_1024bit_block": recommended_output_bits * 85,
        },
        "b_link": {
            "mean_abs_interchannel_corr": b_res["mean_abs_interchannel_corr"],
            "max_abs_interchannel_corr": b_res["max_abs_interchannel_corr"],
            "acf_lag_1": b_res["acf_values"][1],
            "acf_lag_8": b_res["acf_values"][8],
            "acf_lag_64": b_res["acf_values"][64],
        },
    }


def save_topology_svgs() -> None:
    a_svg = FIG_DIR / "chapter2_a_link_topology.svg"
    b_svg = FIG_DIR / "chapter2_b_link_topology.svg"
    a_svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="520" viewBox="0 0 1280 520">
<rect width="1280" height="520" fill="white"/>
<text x="40" y="46" font-size="28" font-family="Helvetica, Arial, sans-serif" fill="#1a1a1a">图 2-1 认证链路 A：平衡探测与基切换光路拓扑图</text>
<rect x="40" y="90" width="1180" height="360" rx="18" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<rect x="80" y="200" width="120" height="70" rx="12" fill="#dbeafe" stroke="#1d4ed8" stroke-width="2"/>
<text x="106" y="242" font-size="22" font-family="Helvetica, Arial, sans-serif">LO 激光器</text>
<line x1="200" y1="235" x2="300" y2="235" stroke="#1d4ed8" stroke-width="4"/>
<rect x="300" y="200" width="120" height="70" rx="12" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
<text x="333" y="242" font-size="22" font-family="Helvetica, Arial, sans-serif">PM</text>
<line x1="420" y1="235" x2="520" y2="235" stroke="#0284c7" stroke-width="4"/>
<polygon points="520,175 590,235 520,295" fill="#fef3c7" stroke="#b45309" stroke-width="2"/>
<text x="534" y="243" font-size="18" font-family="Helvetica, Arial, sans-serif">50:50</text>
<line x1="590" y1="235" x2="700" y2="170" stroke="#b45309" stroke-width="4"/>
<line x1="590" y1="235" x2="700" y2="300" stroke="#b45309" stroke-width="4"/>
<rect x="700" y="130" width="140" height="70" rx="12" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
<rect x="700" y="270" width="140" height="70" rx="12" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
<text x="736" y="173" font-size="22" font-family="Helvetica, Arial, sans-serif">PD1</text>
<text x="736" y="313" font-size="22" font-family="Helvetica, Arial, sans-serif">PD2</text>
<line x1="840" y1="165" x2="935" y2="165" stroke="#15803d" stroke-width="4"/>
<line x1="840" y1="305" x2="935" y2="305" stroke="#15803d" stroke-width="4"/>
<rect x="935" y="190" width="150" height="90" rx="12" fill="#fae8ff" stroke="#9333ea" stroke-width="2"/>
<text x="968" y="232" font-size="22" font-family="Helvetica, Arial, sans-serif">平衡 TIA</text>
<text x="980" y="258" font-size="18" font-family="Helvetica, Arial, sans-serif">CMRR &gt; 40 dB</text>
<line x1="1085" y1="235" x2="1160" y2="235" stroke="#9333ea" stroke-width="4"/>
<rect x="1160" y="200" width="80" height="70" rx="12" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
<text x="1178" y="242" font-size="20" font-family="Helvetica, Arial, sans-serif">ADC</text>
<text x="112" y="120" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#334155">本振相位由 PM 离散切换，测量真空态正交分量</text>
<text x="705" y="390" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#334155">差分探测抑制本振过剩噪声，输出进入高保真采样链</text>
</svg>""",
        encoding="utf-8",
    )
    b_svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="620" viewBox="0 0 1280 620">
<rect width="1280" height="620" fill="white"/>
<text x="40" y="46" font-size="28" font-family="Helvetica, Arial, sans-serif" fill="#1a1a1a">图 2-2 高速链路 B：AWG 复用与多通道 AMZI 干涉结构示意图</text>
<rect x="40" y="90" width="1180" height="460" rx="18" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<rect x="70" y="140" width="180" height="320" rx="16" fill="#dbeafe" stroke="#1d4ed8" stroke-width="2"/>
<text x="95" y="185" font-size="24" font-family="Helvetica, Arial, sans-serif">多通道激光阵列</text>
<text x="110" y="225" font-size="20" font-family="Helvetica, Arial, sans-serif">λ1 ... λ8</text>
<text x="85" y="270" font-size="18" font-family="Helvetica, Arial, sans-serif">相位扩散源</text>
<text x="85" y="300" font-size="18" font-family="Helvetica, Arial, sans-serif">Gain-switched</text>
<line x1="250" y1="300" x2="380" y2="300" stroke="#1d4ed8" stroke-width="4"/>
<rect x="380" y="220" width="170" height="160" rx="16" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
<text x="440" y="270" font-size="24" font-family="Helvetica, Arial, sans-serif">AWG</text>
<text x="412" y="310" font-size="18" font-family="Helvetica, Arial, sans-serif">密集波分复用</text>
<line x1="550" y1="300" x2="680" y2="300" stroke="#0284c7" stroke-width="4"/>
<rect x="680" y="130" width="220" height="340" rx="16" fill="#fef3c7" stroke="#b45309" stroke-width="2"/>
<text x="725" y="175" font-size="24" font-family="Helvetica, Arial, sans-serif">并行 AMZI 阵列</text>
<line x1="710" y1="225" x2="870" y2="225" stroke="#b45309" stroke-width="3"/>
<line x1="710" y1="285" x2="870" y2="285" stroke="#b45309" stroke-width="3"/>
<line x1="710" y1="345" x2="870" y2="345" stroke="#b45309" stroke-width="3"/>
<line x1="710" y1="405" x2="870" y2="405" stroke="#b45309" stroke-width="3"/>
<text x="720" y="215" font-size="16" font-family="Helvetica, Arial, sans-serif">ch1/ch2</text>
<text x="720" y="275" font-size="16" font-family="Helvetica, Arial, sans-serif">ch3/ch4</text>
<text x="720" y="335" font-size="16" font-family="Helvetica, Arial, sans-serif">ch5/ch6</text>
<text x="720" y="395" font-size="16" font-family="Helvetica, Arial, sans-serif">ch7/ch8</text>
<line x1="900" y1="300" x2="1010" y2="300" stroke="#b45309" stroke-width="4"/>
<rect x="1010" y="200" width="120" height="200" rx="16" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
<text x="1040" y="255" font-size="24" font-family="Helvetica, Arial, sans-serif">PD +</text>
<text x="1033" y="290" font-size="24" font-family="Helvetica, Arial, sans-serif">CMP</text>
<text x="1032" y="330" font-size="18" font-family="Helvetica, Arial, sans-serif">2 Gbps/路</text>
<line x1="1130" y1="300" x2="1200" y2="300" stroke="#15803d" stroke-width="4"/>
<text x="920" y="470" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="#334155">6-8 路并行，总原始采样率约 16 Gbps</text>
</svg>""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    fig_dir = resolve_output_dir(args.output_dir)
    summary_path = fig_dir / "chapter2_simulation_summary.json"
    texts = build_text(args.locale)
    ensure_dirs(fig_dir)
    rng = np.random.default_rng(20260414)

    a_res = simulate_a_link(rng)
    b_res = simulate_b_link(rng)
    summary = create_summary(a_res, b_res)

    draw_line_chart(
        fig_dir / "chapter2_sim_a_min_entropy_vs_cmrr.png",
        np.array(a_res["cmrr_db"]),
        np.array(a_res["worst_case_hmin_bits_per_12bit_sample"]),
        str(texts["a_line_title"]),
        str(texts["a_line_xlabel"]),
        str(texts["a_line_ylabel"]),
        BLUE,
        list(texts["a_line_notes"]),
    )

    labels = list(texts["channel_labels"])
    draw_heatmap(
        fig_dir / "chapter2_sim_b_corr_heatmap.png",
        np.array(b_res["corr_matrix"]),
        labels,
        str(texts["b_heatmap_title"]),
        [
            f"{texts['b_heatmap_notes'][0]} = {b_res['mean_abs_interchannel_corr']:.4f}",
            f"{texts['b_heatmap_notes'][1]} = {b_res['max_abs_interchannel_corr']:.4f}",
        ],
    )

    draw_pdf_acf(
        fig_dir / "chapter2_sim_pdf_acf.png",
        np.array(a_res["pdf_x"]),
        np.array(a_res["pdf_y"]),
        np.array(b_res["acf_lags"]),
        np.array(b_res["acf_values"]),
        texts,
    )

    create_summary(a_res, b_res)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    create_summary(a_res, b_res)
    if args.with_svg:
        save_topology_svgs()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
