from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
SUMMARY_PATH = FIG_DIR / "chapter5_simulation_summary.json"

CALL_FLOW_FIG = FIG_DIR / "chapter5_nas_call_flow.svg"
TIMELINE_FIG = FIG_DIR / "chapter5_io_rng_timeline.png"

WIDTH = 1560
HEIGHT = 1180
BG = "#f4f7fb"
CARD_BG = "#ffffff"
FRAME = "#d7e1ec"
FG = "#1a1a1a"
GRID = "#d8dde6"
BLUE = "#2f6fed"
GREEN = "#1b9e77"
ORANGE = "#ff8c42"
RED = "#d7263d"
PURPLE = "#7a4dd8"
GREY = "#485564"
LIGHT_BLUE = "#e9f0ff"
LIGHT_GREEN = "#eaf8f2"
LIGHT_RED = "#ffe7eb"


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
            "random_title": "随机 4K 业务负载：I/O 速率与随机数消耗速率",
            "seq_title": "顺序 1M 业务负载：I/O 速率与随机数消耗速率",
            "backlog_title": "顺序 1M 下的速率赤字积累：Balanced vs Throughput",
            "xlabel": "时间 / s",
            "ylabel_rate": "速率 / Gbps",
            "ylabel_backlog": "积压 / Gbit",
            "legend_io": "I/O 吞吐",
            "legend_rng": "随机数消耗",
            "legend_bal": "Balanced = 8 Gbps",
            "legend_thr": "Throughput = 10 Gbps",
            "backlog_bal": "Balanced 积压",
            "backlog_thr": "Throughput 积压",
            "footer_1": "上界估算规则：将主机可见加密数据面吞吐按 1 bit 数据流对应 1 bit fast pad 消耗计算，并附加 2% 封装余量。",
            "footer_2": "当前工作区未提供实机 trace，本图使用与 4-bay NVMe NAS FIO 轮廓一致的代表性 trace 进行验证。",
        }
    return {
        "random_title": "Random 4K workload: I/O rate and random-service demand",
        "seq_title": "Sequential 1M workload: I/O rate and random-service demand",
        "backlog_title": "Sequential 1M deficit accumulation: Balanced vs Throughput",
        "xlabel": "Time / s",
        "ylabel_rate": "Rate / Gbps",
        "ylabel_backlog": "Backlog / Gbit",
        "legend_io": "Host-visible I/O",
        "legend_rng": "Random demand",
        "legend_bal": "Balanced = 8 Gbps",
        "legend_thr": "Throughput = 10 Gbps",
        "backlog_bal": "Balanced backlog",
        "backlog_thr": "Throughput backlog",
        "footer_1": "Upper-bound rule: host-visible encrypted traffic is mapped to fast-pad demand at 1 bit per bit of data, plus a 2% framing margin.",
        "footer_2": "No device trace is available in the current workspace, so the figure uses representative traces aligned with 4-bay NVMe NAS FIO profiles.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate chapter 5 NAS workload figures.")
    parser.add_argument("--locale", choices=("en", "zh"), default="zh")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--with-svg", action="store_true", help="Also regenerate the legacy NAS call-flow SVG.")
    return parser.parse_args()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def save_call_flow_svg(path: Path) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1420" height="720" viewBox="0 0 1420 720">
  <rect width="1420" height="720" fill="#ffffff"/>
  <text x="710" y="42" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">图 5-1 四盘位 NAS 中控制面与数据面的双轨调用关系</text>

  <rect x="40" y="90" width="280" height="560" rx="18" fill="#eef4ff" stroke="{BLUE}" stroke-width="3"/>
  <text x="180" y="126" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">NAS 应用层</text>
  <rect x="72" y="168" width="216" height="134" rx="12" fill="#ffffff" stroke="{BLUE}" stroke-width="2"/>
  <text x="180" y="208" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Control Plane</text>
  <text x="180" y="236" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">系统启动熵池 / Root Seed</text>
  <text x="180" y="258" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">主密钥 / KEK / 证书 Nonce</text>
  <rect x="72" y="354" width="216" height="170" rx="12" fill="#ffffff" stroke="{BLUE}" stroke-width="2"/>
  <text x="180" y="394" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Data Plane</text>
  <text x="180" y="422" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">dm-crypt / SPDK / RAID / NVMe</text>
  <text x="180" y="444" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">Balanced / Throughput</text>
  <text x="180" y="466" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">实时加密数据面</text>
  <rect x="72" y="562" width="216" height="60" rx="10" fill="#fff4de" stroke="{ORANGE}" stroke-width="2"/>
  <text x="180" y="600" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">普通业务进程不得直接越权切换模式</text>

  <rect x="390" y="90" width="310" height="560" rx="18" fill="#f6fbf8" stroke="{GREEN}" stroke-width="3"/>
  <text x="545" y="126" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">驱动层 / 访问控制隔离墙</text>
  <rect x="424" y="168" width="242" height="150" rx="12" fill="#ffffff" stroke="{GREEN}" stroke-width="2"/>
  <text x="545" y="206" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">/dev/qrng_cert</text>
  <text x="545" y="234" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">Certified 模式主节点</text>
  <text x="545" y="258" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">阻塞式 read + 健康状态绑定</text>
  <text x="545" y="282" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">仅控制面与密钥服务可访问</text>
  <rect x="424" y="382" width="242" height="170" rx="12" fill="#ffffff" stroke="{GREEN}" stroke-width="2"/>
  <text x="545" y="420" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">/dev/qrng_fast</text>
  <text x="545" y="448" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">Balanced / Throughput 数据节点</text>
  <text x="545" y="472" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">mmap + SG DMA + 零拷贝</text>
  <text x="545" y="496" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">失效时返回 ENODEV，不回退到 cert</text>
  <rect x="448" y="588" width="194" height="36" rx="8" fill="#ffe7eb" stroke="{RED}" stroke-width="2"/>
  <text x="545" y="611" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">cert / fast 不共享用户可见寄存器视图</text>

  <rect x="770" y="90" width="280" height="560" rx="18" fill="#fffaf1" stroke="{ORANGE}" stroke-width="3"/>
  <text x="910" y="126" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">板卡内部模式映射</text>
  <rect x="804" y="168" width="212" height="104" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="910" y="202" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Certified</text>
  <text x="910" y="228" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">仅 A 链路激活</text>
  <text x="910" y="250" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">0.5–2 Gbps</text>
  <rect x="804" y="314" width="212" height="114" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="910" y="350" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Balanced</text>
  <text x="910" y="376" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">B 供数，A 监督 + 重播种</text>
  <text x="910" y="398" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">默认全局数据加密</text>
  <rect x="804" y="470" width="212" height="114" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="910" y="506" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Throughput / OTP-rate</text>
  <text x="910" y="532" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">B 激进抽取</text>
  <text x="910" y="554" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">Fast pad mode，仅工程安全声明</text>

  <rect x="1120" y="90" width="250" height="560" rx="18" fill="#f7f7f9" stroke="{GREY}" stroke-width="3"/>
  <text x="1245" y="126" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">4-bay NVMe 阵列</text>
  <rect x="1150" y="182" width="190" height="84" rx="10" fill="#ffffff" stroke="{GREY}" stroke-width="2"/>
  <text x="1245" y="218" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">NVMe 0 / 1</text>
  <text x="1245" y="242" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">PCIe x4 + RAID 条带</text>
  <rect x="1150" y="312" width="190" height="84" rx="10" fill="#ffffff" stroke="{GREY}" stroke-width="2"/>
  <text x="1245" y="348" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">NVMe 2 / 3</text>
  <text x="1245" y="372" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">主机可见有效加密数据面</text>
  <rect x="1150" y="460" width="190" height="96" rx="10" fill="#fff4de" stroke="{ORANGE}" stroke-width="2"/>
  <text x="1245" y="496" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">速率基准</text>
  <text x="1245" y="522" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">按主机可见 I/O 吞吐</text>
  <text x="1245" y="544" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">不按裸介质峰值叠加</text>

  <line x1="288" y1="236" x2="424" y2="236" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="288" y1="438" x2="424" y2="462" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="666" y1="236" x2="804" y2="220" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="666" y1="462" x2="804" y2="372" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="666" y1="462" x2="804" y2="526" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="1016" y1="370" x2="1150" y2="354" stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="1016" y1="526" x2="1150" y2="502" stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow)"/>
  <rect x="335" y="310" width="30" height="118" fill="#ffe7eb" stroke="{RED}" stroke-width="2"/>
  <line x1="350" y1="322" x2="350" y2="416" stroke="{RED}" stroke-width="3"/>
  <line x1="340" y1="334" x2="360" y2="334" stroke="{RED}" stroke-width="3"/>
  <line x1="340" y1="356" x2="360" y2="356" stroke="{RED}" stroke-width="3"/>
  <line x1="340" y1="378" x2="360" y2="378" stroke="{RED}" stroke-width="3"/>
  <line x1="340" y1="400" x2="360" y2="400" stroke="{RED}" stroke-width="3"/>
  <text x="350" y="448" text-anchor="middle" font-size="13" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">ACL</text>

  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#44515c"/>
    </marker>
  </defs>
</svg>
"""
    write_text(path, svg)


def draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, xlabel: str, ylabel: str) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline="#444444", width=2)
    draw.line((x0 + 90, y1 - 60, x1 - 24, y1 - 60), fill=FG, width=3)
    draw.line((x0 + 90, y1 - 60, x0 + 90, y0 + 30), fill=FG, width=3)
    draw.text((x0 + 90, y0 - 40), title, fill=FG, font=get_font(28))
    draw.text((x1 - 180, y1 - 48), xlabel, fill=FG, font=get_font(22))
    draw.text((x0 + 6, y0 + 36), ylabel, fill=FG, font=get_font(22))
    for i in range(1, 5):
        y = y0 + 30 + i * (y1 - y0 - 90) / 5
        x = x0 + 90 + i * (x1 - x0 - 114) / 5
        draw.line((x0 + 90, y, x1 - 24, y), fill=GRID, width=1)
        draw.line((x, y0 + 30, x, y1 - 60), fill=GRID, width=1)


def scale_points(xs: np.ndarray, ys: np.ndarray, box: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    left = x0 + 90
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


def build_random4k_trace(times: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    base = 4.9 + 0.55 * np.sin(2 * np.pi * times / 18.0) + 0.28 * np.sin(2 * np.pi * times / 4.8)
    burst = np.where((times > 12.0) & (times < 18.0), 0.75, 0.0) + np.where((times > 34.0) & (times < 40.0), 0.55, 0.0)
    noise = rng.normal(0.0, 0.14, size=times.size)
    return np.clip(base + burst + noise, 3.8, 6.6)


def build_seq1m_trace(times: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    ramp = np.piecewise(
        times,
        [times < 10.0, (times >= 10.0) & (times < 24.0), (times >= 24.0) & (times < 42.0), times >= 42.0],
        [
            lambda t: 7.1 + 0.10 * t,
            lambda t: 8.2 + 0.07 * (t - 10.0),
            lambda t: 9.15 - 0.02 * (t - 24.0),
            lambda t: 8.75 + 0.03 * (t - 42.0),
        ],
    )
    ripple = 0.24 * np.sin(2 * np.pi * times / 8.0) + 0.11 * np.sin(2 * np.pi * times / 2.6)
    noise = rng.normal(0.0, 0.08, size=times.size)
    return np.clip(ramp + ripple + noise, 6.9, 9.6)


def backlog_profile(demand: np.ndarray, capacity: float, dt_s: float) -> np.ndarray:
    backlog = np.zeros_like(demand)
    current = 0.0
    for i, d in enumerate(demand):
        current = max(0.0, current + (float(d) - capacity) * dt_s)
        backlog[i] = current
    return backlog


def trace_stats(io_rate: np.ndarray, demand: np.ndarray, balanced_backlog: np.ndarray, throughput_backlog: np.ndarray, throughput_capacity: float) -> dict[str, float]:
    return {
        "mean_io_gbps": float(io_rate.mean()),
        "peak_io_gbps": float(io_rate.max()),
        "mean_rng_demand_gbps": float(demand.mean()),
        "peak_rng_demand_gbps": float(demand.max()),
        "min_throughput_headroom_gbps": float(throughput_capacity - demand.max()),
        "balanced_max_backlog_gbit": float(balanced_backlog.max()),
        "throughput_max_backlog_gbit": float(throughput_backlog.max()),
    }


def render_timeline(path: Path, times: np.ndarray, random4k: np.ndarray, seq1m: np.ndarray, demand_random: np.ndarray, demand_seq: np.ndarray, balanced_cap: float, throughput_cap: float, texts: dict[str, object]) -> dict[str, dict[str, float]]:
    dt_s = float(times[1] - times[0])
    backlog_random_bal = backlog_profile(demand_random, balanced_cap, dt_s)
    backlog_random_thr = backlog_profile(demand_random, throughput_cap, dt_s)
    backlog_seq_bal = backlog_profile(demand_seq, balanced_cap, dt_s)
    backlog_seq_thr = backlog_profile(demand_seq, throughput_cap, dt_s)

    img, draw = prepare_canvas()

    box1 = (70, 110, 1490, 400)
    box2 = (70, 460, 1490, 750)
    box3 = (70, 810, 1490, 1110)

    draw_axes(draw, box1, str(texts["random_title"]), str(texts["xlabel"]), str(texts["ylabel_rate"]))
    draw_axes(draw, box2, str(texts["seq_title"]), str(texts["xlabel"]), str(texts["ylabel_rate"]))
    draw_axes(draw, box3, str(texts["backlog_title"]), str(texts["xlabel"]), str(texts["ylabel_backlog"]))

    for box, io_rate, demand, title_mode in (
        (box1, random4k, demand_random, "Random 4K"),
        (box2, seq1m, demand_seq, "Sequential 1M"),
    ):
        io_pts = scale_points(times, io_rate, box)
        demand_pts = scale_points(times, demand, box)
        cap_bal = scale_points(times, np.full_like(times, balanced_cap), box)
        cap_thr = scale_points(times, np.full_like(times, throughput_cap), box)
        draw.line(io_pts, fill=BLUE, width=4)
        draw.line(demand_pts, fill=ORANGE, width=4)
        draw.line(cap_bal, fill=PURPLE, width=3)
        draw.line(cap_thr, fill=GREEN, width=3)
        x0, y0, x1, y1 = box
        draw.text((x1 - 330, y0 + 10), str(texts["legend_io"]), fill=BLUE, font=get_font(20))
        draw.text((x1 - 330, y0 + 36), str(texts["legend_rng"]), fill=ORANGE, font=get_font(20))
        draw.text((x1 - 330, y0 + 62), str(texts["legend_bal"]), fill=PURPLE, font=get_font(20))
        draw.text((x1 - 330, y0 + 88), str(texts["legend_thr"]), fill=GREEN, font=get_font(20))

    back_bal_pts = scale_points(times, backlog_seq_bal, box3)
    back_thr_pts = scale_points(times, backlog_seq_thr, box3)
    draw.line(back_bal_pts, fill=PURPLE, width=4)
    draw.line(back_thr_pts, fill=GREEN, width=4)
    draw.text((1180, 820), str(texts["backlog_bal"]), fill=PURPLE, font=get_font(20))
    draw.text((1180, 846), str(texts["backlog_thr"]), fill=GREEN, font=get_font(20))

    footer_y = 1130
    draw.text((80, footer_y), str(texts["footer_1"]), fill=FG, font=get_font(19))
    draw.text((80, footer_y + 28), str(texts["footer_2"]), fill=FG, font=get_font(19))
    img.save(path)

    return {
        "random4k": trace_stats(random4k, demand_random, backlog_random_bal, backlog_random_thr, throughput_cap),
        "seq1m": trace_stats(seq1m, demand_seq, backlog_seq_bal, backlog_seq_thr, throughput_cap),
    }


def build_summary(trace_stats_dict: dict[str, dict[str, float]]) -> dict[str, object]:
    return {
        "trace_source": "当前工作区未提供实机 4-bay NAS I/O trace；本节采用与 FIO 随机 4K / 顺序 1M 工作负载轮廓一致的代表性 trace。",
        "rng_consumption_rule": "按主机可见加密数据面 1 bit 流量对应 1 bit fast pad 消耗计，并加 2% 封装余量。",
        "mode_targets_gbps": {
            "certified_range": [0.5, 2.0],
            "balanced_reference": 8.0,
            "throughput_reference": 10.0,
        },
        "random4k_trace": trace_stats_dict["random4k"],
        "seq1m_trace": trace_stats_dict["seq1m"],
        "key_findings": {
            "random4k_supported_by_balanced": trace_stats_dict["random4k"]["balanced_max_backlog_gbit"] == 0.0,
            "seq1m_supported_by_throughput_without_backlog": trace_stats_dict["seq1m"]["throughput_max_backlog_gbit"] == 0.0,
            "seq1m_requires_throughput_for_zero_backlog": trace_stats_dict["seq1m"]["balanced_max_backlog_gbit"] > 0.0,
        },
    }


def main() -> None:
    args = parse_args()
    fig_dir = resolve_output_dir(args.output_dir)
    summary_path = fig_dir / "chapter5_simulation_summary.json"
    call_flow_fig = fig_dir / "chapter5_nas_call_flow.svg"
    timeline_fig = fig_dir / "chapter5_io_rng_timeline.png"
    texts = build_text(args.locale)
    ensure_dirs(fig_dir)
    if args.with_svg:
        save_call_flow_svg(call_flow_fig)
    rng = np.random.default_rng(20260414)
    times = np.arange(0.0, 60.0, 0.25)
    random4k = build_random4k_trace(times, rng)
    seq1m = build_seq1m_trace(times, rng)
    demand_random = np.clip(random4k * 1.02, 0.0, None)
    demand_seq = np.clip(seq1m * 1.02, 0.0, None)
    stats = render_timeline(timeline_fig, times, random4k, seq1m, demand_random, demand_seq, balanced_cap=8.0, throughput_cap=10.0, texts=texts)
    summary = build_summary(stats)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
