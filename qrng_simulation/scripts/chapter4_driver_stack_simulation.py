from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
SUMMARY_PATH = FIG_DIR / "chapter4_simulation_summary.json"


DEVICE_FIG = FIG_DIR / "chapter4_driver_stack_architecture.svg"
STATE_FIG = FIG_DIR / "chapter4_mode_switch_state_machine.svg"
BLACKOUT_FIG = FIG_DIR / "chapter4_blackout_jitter.png"
TIMELINE_FIG = FIG_DIR / "chapter4_queue_timeline.png"

WIDTH = 1520
HEIGHT = 880
BG = "#f4f7fb"
CARD_BG = "#ffffff"
FRAME = "#d7e1ec"
FG = "#1a1a1a"
GRID = "#d8dde6"
BLUE = "#2f6fed"
GREEN = "#1b9e77"
ORANGE = "#ff8c42"
RED = "#d7263d"
GOLD = "#f6c344"
GREY = "#485564"
LIGHT_BLUE = "#cfe0ff"
LIGHT_RED = "#ffe7eb"


def ensure_dirs(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)


def resolve_output_dir(output_dir: str | None) -> Path:
    return Path(output_dir) if output_dir else FIG_DIR


def prepare_canvas(height: int = HEIGHT) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)
    try:
        draw.rounded_rectangle((24, 24, WIDTH - 24, height - 24), radius=28, fill=CARD_BG, outline=FRAME, width=2)
    except AttributeError:
        draw.rectangle((24, 24, WIDTH - 24, height - 24), fill=CARD_BG, outline=FRAME, width=2)
    return img, draw


def get_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_text(locale: str) -> dict[str, object]:
    if locale == "zh":
        return {
            "blackout_left_title": "模式切换黑障时间抖动曲线",
            "blackout_left_xlabel": "切换事件编号",
            "blackout_left_ylabel": "黑障时间 / ms",
            "blackout_right_title": "黑障时间累积分布",
            "blackout_right_xlabel": "黑障时间 / ms",
            "blackout_right_ylabel": "CDF",
            "blackout_legend_1": "点颜色表示 CPU 负载因子；左图红线为 2 ms 规格上限，横线给出 P95 / P99。",
            "blackout_legend_2": "右图为黑障时间经验 CDF，可直接读取系统切换抖动的尾部风险。",
            "queue_title": "生产者-消费者并发模型下的环形缓冲占用",
            "queue_xlabel": "时间 / ms",
            "queue_ylabel": "队列 / 包",
            "state_title": "模式切换期间的阻断状态",
            "state_xlabel": "时间 / ms",
            "state_ylabel": "状态通道",
            "window_title": "系统级黑障窗口与恢复点",
            "window_xlabel": "时间 / ms",
            "window_ylabel": "服务可用性",
            "state_labels": ["输出有效", "-EAGAIN", "ZEROIZE", "AUDIT LOG"],
            "blackout_window": "系统级黑障窗口",
            "timeline_footer": "代表性切换事件: 黑障 {blackout:.3f} ms, Zeroize 前最大待冲刷包数 {flushed:.1f}。",
        }
    return {
        "blackout_left_title": "Mode-switch blackout jitter",
        "blackout_left_xlabel": "Switch event index",
        "blackout_left_ylabel": "Blackout / ms",
        "blackout_right_title": "Blackout empirical CDF",
        "blackout_right_xlabel": "Blackout / ms",
        "blackout_right_ylabel": "CDF",
        "blackout_legend_1": "Dot color encodes CPU load. The left panel shows the 2 ms limit and the P95 / P99 reference lines.",
        "blackout_legend_2": "The right panel is the empirical CDF, so tail-risk of switch jitter can be read directly.",
        "queue_title": "Ring-buffer occupancy under the producer-consumer model",
        "queue_xlabel": "Time / ms",
        "queue_ylabel": "Queue / packets",
        "state_title": "Blocking states during a mode transition",
        "state_xlabel": "Time / ms",
        "state_ylabel": "State lane",
        "window_title": "System blackout window and recovery point",
        "window_xlabel": "Time / ms",
        "window_ylabel": "Service availability",
        "state_labels": ["Output valid", "-EAGAIN", "ZEROIZE", "AUDIT LOG"],
        "blackout_window": "System blackout window",
        "timeline_footer": "Representative switch event: blackout {blackout:.3f} ms, max packets flushed before zeroize {flushed:.1f}.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate chapter 4 driver and mode-switch figures.")
    parser.add_argument("--locale", choices=("en", "zh"), default="zh")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--with-svg", action="store_true", help="Also regenerate the legacy SVG diagrams.")
    return parser.parse_args()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def save_driver_stack_svg(path: Path) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1380" height="660" viewBox="0 0 1380 660">
  <rect width="1380" height="660" fill="#ffffff"/>
  <text x="690" y="42" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">图 4-1 驱动栈与双设备节点隔离结构</text>

  <rect x="40" y="90" width="260" height="510" rx="18" fill="#eef4ff" stroke="{BLUE}" stroke-width="3"/>
  <text x="170" y="125" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">用户态 / 应用层</text>
  <rect x="70" y="160" width="200" height="96" rx="12" fill="#ffffff" stroke="{BLUE}" stroke-width="2"/>
  <text x="170" y="194" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">控制平面</text>
  <text x="170" y="220" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">rngd / 启动熵池 / Root Key</text>
  <rect x="70" y="300" width="200" height="118" rx="12" fill="#ffffff" stroke="{BLUE}" stroke-width="2"/>
  <text x="170" y="334" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">数据平面</text>
  <text x="170" y="362" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">dm-crypt / SPDK / 用户态 I/O</text>
  <text x="170" y="386" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">只允许映射 Fast 缓冲区</text>
  <rect x="70" y="464" width="200" height="96" rx="12" fill="#fff7eb" stroke="{ORANGE}" stroke-width="2"/>
  <text x="170" y="499" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">策略边界</text>
  <text x="170" y="525" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">控制面不得读取 Fast 审计寄存器</text>
  <text x="170" y="547" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">数据面不得回退读取 Cert</text>

  <rect x="360" y="90" width="300" height="510" rx="18" fill="#f6fbf8" stroke="{GREEN}" stroke-width="3"/>
  <text x="510" y="125" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">OS 内核 / 设备节点隔离墙</text>
  <rect x="390" y="160" width="240" height="134" rx="12" fill="#ffffff" stroke="{GREEN}" stroke-width="2"/>
  <text x="510" y="192" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">/dev/qrng_cert</text>
  <text x="510" y="220" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">阻塞式 read() + poll()</text>
  <text x="510" y="244" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">每次读前强制查询健康状态</text>
  <text x="510" y="268" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">超时则返回 -EAGAIN / -EIO</text>
  <rect x="390" y="338" width="240" height="154" rx="12" fill="#ffffff" stroke="{GREEN}" stroke-width="2"/>
  <text x="510" y="370" text-anchor="middle" font-size="20" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">/dev/qrng_fast</text>
  <text x="510" y="398" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">mmap() + SG DMA + 零拷贝</text>
  <text x="510" y="422" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">独立 MMIO BAR / IOMMU 域</text>
  <text x="510" y="446" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">ioctl: 模式切换 / 审计查询</text>
  <rect x="390" y="528" width="240" height="46" rx="10" fill="#ffe7eb" stroke="{RED}" stroke-width="2"/>
  <text x="510" y="557" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">物理与逻辑接口绝对分离</text>

  <rect x="720" y="90" width="300" height="510" rx="18" fill="#fffaf1" stroke="{ORANGE}" stroke-width="3"/>
  <text x="870" y="125" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">驱动核心与审计路径</text>
  <rect x="750" y="160" width="240" height="108" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="870" y="194" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">模式切换状态机</text>
  <text x="870" y="220" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">BLOCK_IO → ZEROIZE</text>
  <text x="870" y="244" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">→ REBUILD → AUDIT → RESUME</text>
  <rect x="750" y="304" width="240" height="108" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="870" y="338" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">双缓冲 DMA 管理</text>
  <text x="870" y="364" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">环形描述符池 / 代际标记</text>
  <text x="870" y="388" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">切换时强制 flush 旧代包</text>
  <rect x="750" y="448" width="240" height="112" rx="12" fill="#ffffff" stroke="{ORANGE}" stroke-width="2"/>
  <text x="870" y="482" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">审计与告警</text>
  <text x="870" y="508" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">dmesg + 受保护日志</text>
  <text x="870" y="532" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">记录模式、操作者、耗时、故障码</text>

  <rect x="1080" y="90" width="260" height="510" rx="18" fill="#f7f7f9" stroke="{GREY}" stroke-width="3"/>
  <text x="1210" y="125" text-anchor="middle" font-size="22" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">硬件 / PCIe 端点</text>
  <rect x="1110" y="160" width="200" height="110" rx="12" fill="#ffffff" stroke="{GREY}" stroke-width="2"/>
  <text x="1210" y="192" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Cert BAR + FIFO</text>
  <text x="1210" y="218" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">A 链路健康状态 / 小块读</text>
  <text x="1210" y="242" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">不可被 Fast DMA 访问</text>
  <rect x="1110" y="314" width="200" height="110" rx="12" fill="#ffffff" stroke="{GREY}" stroke-width="2"/>
  <text x="1210" y="346" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Fast BAR + DMA</text>
  <text x="1210" y="372" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">SG 描述符 / 零拷贝环</text>
  <text x="1210" y="396" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">只读数据面映射</text>
  <rect x="1110" y="468" width="200" height="92" rx="12" fill="#fff4de" stroke="{GOLD}" stroke-width="2"/>
  <text x="1210" y="500" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">Zeroize 引擎</text>
  <text x="1210" y="526" text-anchor="middle" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">RAM 覆写 / FIFO 冲刷 / DMA quiesce</text>

  <line x1="270" y1="210" x2="390" y2="210" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="270" y1="356" x2="390" y2="410" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="630" y1="220" x2="750" y2="220" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="630" y1="416" x2="750" y2="358" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="990" y1="214" x2="1110" y2="214" stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="990" y1="358" x2="1110" y2="369" stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="990" y1="514" x2="1110" y2="514" stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow)"/>

  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#44515c"/>
    </marker>
  </defs>
</svg>
"""
    write_text(path, svg)


def save_state_machine_svg(path: Path) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1460" height="620" viewBox="0 0 1460 620">
  <rect width="1460" height="620" fill="#ffffff"/>
  <text x="730" y="42" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">图 4-2 模式切换安全状态机</text>

  <rect x="70" y="238" width="200" height="90" rx="18" fill="#eef4ff" stroke="{BLUE}" stroke-width="3"/>
  <text x="170" y="286" text-anchor="middle" font-size="24" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">RUNNING</text>
  <text x="170" y="312" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#506070">RUNNING_CERT / RUNNING_FAST</text>

  <rect x="330" y="238" width="190" height="90" rx="18" fill="#f6fbf8" stroke="{GREEN}" stroke-width="3"/>
  <text x="425" y="286" text-anchor="middle" font-size="24" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">BLOCK_IO</text>
  <text x="425" y="312" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#506070">冻结新请求 / Pending 返回 -EAGAIN</text>

  <rect x="580" y="216" width="210" height="134" rx="18" fill="#ffe7eb" stroke="{RED}" stroke-width="4"/>
  <text x="685" y="270" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">ZEROIZE</text>
  <text x="685" y="302" text-anchor="middle" font-size="17" font-family="Arial, Helvetica, sans-serif" fill="#506070">覆写 Key RAM / 冲刷 FIFO</text>
  <text x="685" y="326" text-anchor="middle" font-size="17" font-family="Arial, Helvetica, sans-serif" fill="#506070">DMA quiesce / 丢弃旧代包</text>

  <rect x="850" y="238" width="200" height="90" rx="18" fill="#eef4ff" stroke="{BLUE}" stroke-width="3"/>
  <text x="950" y="286" text-anchor="middle" font-size="24" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">REBUILD</text>
  <text x="950" y="312" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#506070">重建 Extractor / Seed 上下文</text>

  <rect x="1110" y="216" width="220" height="134" rx="18" fill="#fff1d6" stroke="{ORANGE}" stroke-width="4"/>
  <text x="1220" y="270" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">AUDIT LOG</text>
  <text x="1220" y="302" text-anchor="middle" font-size="17" font-family="Arial, Helvetica, sans-serif" fill="#506070">记录操作者 / 模式 / 耗时</text>
  <text x="1220" y="326" text-anchor="middle" font-size="17" font-family="Arial, Helvetica, sans-serif" fill="#506070">写入 dmesg 与受保护日志</text>

  <rect x="1120" y="432" width="200" height="90" rx="18" fill="#f6fbf8" stroke="{GREEN}" stroke-width="3"/>
  <text x="1220" y="480" text-anchor="middle" font-size="24" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">RESUME_IO</text>
  <text x="1220" y="506" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#506070">恢复新代数据出流</text>

  <rect x="850" y="432" width="200" height="90" rx="18" fill="#f7f7f9" stroke="{GREY}" stroke-width="3"/>
  <text x="950" y="480" text-anchor="middle" font-size="24" font-family="Arial, Helvetica, sans-serif" fill="#1f2a36">FAULT_HOLD</text>
  <text x="950" y="506" text-anchor="middle" font-size="16" font-family="Arial, Helvetica, sans-serif" fill="#506070">异常则维持阻断，不可部分恢复</text>

  <line x1="270" y1="283" x2="330" y2="283" stroke="#44515c" stroke-width="4" marker-end="url(#arrow)"/>
  <line x1="520" y1="283" x2="580" y2="283" stroke="#44515c" stroke-width="4" marker-end="url(#arrow)"/>
  <line x1="790" y1="283" x2="850" y2="283" stroke="#44515c" stroke-width="4" marker-end="url(#arrow)"/>
  <line x1="1050" y1="283" x2="1110" y2="283" stroke="#44515c" stroke-width="4" marker-end="url(#arrow)"/>
  <line x1="1220" y1="350" x2="1220" y2="432" stroke="#44515c" stroke-width="4" marker-end="url(#arrow)"/>
  <line x1="1110" y1="283" x2="950" y2="432" stroke="#44515c" stroke-width="3" stroke-dasharray="10 8" marker-end="url(#arrow)"/>
  <line x1="685" y1="350" x2="950" y2="432" stroke="#44515c" stroke-width="3" stroke-dasharray="10 8" marker-end="url(#arrow)"/>
  <line x1="950" y1="432" x2="950" y2="328" stroke="#44515c" stroke-width="3" stroke-dasharray="10 8" marker-end="url(#arrow)"/>
  <text x="1010" y="404" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">重建失败 / 审计失败</text>
  <text x="748" y="198" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">安全关键阻断态</text>
  <text x="1240" y="198" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">安全关键阻断态</text>
  <text x="300" y="250" font-size="15" font-family="Arial, Helvetica, sans-serif" fill="#506070">收到模式切换命令</text>

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


def color_from_load(load: float) -> tuple[int, int, int]:
    load = float(np.clip(load, 0.0, 1.0))
    r = int(35 + 210 * load)
    g = int(80 + 160 * (1.0 - load))
    b = int(70 + 110 * (1.0 - abs(load - 0.5) * 2.0))
    return r, g, b


@dataclass
class TrialResult:
    blackout_ms: float
    block_io_us: float
    zeroize_us: float
    rebuild_us: float
    audit_us: float
    resume_us: float
    flushed_packets: int
    stale_after_resume: int
    cpu_load: float


def sample_state_durations(rng: np.random.Generator, cpu_load: float, queue_fill: float) -> tuple[float, float, float, float, float]:
    block_io = 70.0 + 85.0 * cpu_load + 45.0 * queue_fill + rng.normal(0.0, 8.0)
    zeroize = 95.0 + 25.0 * cpu_load + 28.0 * queue_fill + rng.normal(0.0, 6.0)
    rebuild = 330.0 + 260.0 * cpu_load + 140.0 * queue_fill + rng.normal(0.0, 20.0)
    audit = 85.0 + 170.0 * cpu_load + 30.0 * queue_fill + rng.normal(0.0, 15.0)
    resume = 130.0 + 220.0 * cpu_load + 70.0 * queue_fill + rng.normal(0.0, 18.0)
    vals = [block_io, zeroize, rebuild, audit, resume]
    return tuple(max(v, 5.0) for v in vals)


def simulate_blackout_trials(seed: int = 20260414, n_trials: int = 480) -> list[TrialResult]:
    rng = np.random.default_rng(seed)
    results: list[TrialResult] = []
    for _ in range(n_trials):
        cpu_load = float(np.clip(rng.beta(2.4, 1.8), 0.12, 0.98))
        queue_fill = float(np.clip(rng.normal(0.70, 0.15), 0.30, 0.98))
        block_io_us, zeroize_us, rebuild_us, audit_us, resume_us = sample_state_durations(rng, cpu_load, queue_fill)
        scheduler_gap_us = max(30.0, 60.0 + 180.0 * cpu_load + rng.normal(0.0, 15.0))
        blackout_ms = (block_io_us + zeroize_us + rebuild_us + audit_us + resume_us + scheduler_gap_us) / 1000.0
        flushed_packets = int(round(queue_fill * (24.0 + 16.0 * cpu_load)))
        results.append(
            TrialResult(
                blackout_ms=float(blackout_ms),
                block_io_us=float(block_io_us),
                zeroize_us=float(zeroize_us),
                rebuild_us=float(rebuild_us),
                audit_us=float(audit_us),
                resume_us=float(resume_us),
                flushed_packets=flushed_packets,
                stale_after_resume=0,
                cpu_load=cpu_load,
            )
        )
    return results


def simulate_representative_timeline(seed: int = 20260415) -> dict[str, np.ndarray | float]:
    rng = np.random.default_rng(seed)
    dt_ms = 0.02
    total_ms = 8.0
    times = np.arange(0.0, total_ms + dt_ms, dt_ms)
    queue_depth = 64.0
    produce_rate = np.where(times < 1.7, 1.45, np.where(times < 3.0, 0.0, 1.42))
    consume_rate = np.where(times < 1.70, 1.38, np.where(times < 2.88, 0.0, 1.35))

    switch_t0 = 1.70
    block_io_end = 1.82
    zeroize_end = 1.95
    rebuild_end = 2.41
    audit_end = 2.68
    resume_t = 2.88
    new_data_t = 2.96

    queue = np.zeros_like(times)
    output_valid = np.ones_like(times)
    zeroize_flag = np.zeros_like(times)
    audit_flag = np.zeros_like(times)
    eagain_flag = np.zeros_like(times)
    current_queue = 28.0
    flush_packets = 0.0

    for i, t in enumerate(times):
        if t >= block_io_end:
            output_valid[i] = 0.0
            eagain_flag[i] = 1.0
        if block_io_end <= t < zeroize_end:
            current_queue += produce_rate[i]
        elif zeroize_end <= t < rebuild_end:
            zeroize_flag[i] = 1.0
            flush_packets = max(flush_packets, current_queue)
            current_queue = max(0.0, current_queue - 11.0)
        elif rebuild_end <= t < audit_end:
            current_queue = 0.0
        elif audit_end <= t < resume_t:
            audit_flag[i] = 1.0
            current_queue = 0.0
        else:
            if t >= resume_t:
                output_valid[i] = 1.0 if t >= new_data_t else 0.0
                eagain_flag[i] = 0.0 if t >= new_data_t else 1.0
                current_queue = min(queue_depth, max(0.0, current_queue + produce_rate[i] - consume_rate[i] + rng.normal(0.0, 0.18)))
            else:
                current_queue = min(queue_depth, max(0.0, current_queue + produce_rate[i] - consume_rate[i] + rng.normal(0.0, 0.10)))
        queue[i] = current_queue

    return {
        "times_ms": times,
        "queue_packets": queue,
        "output_valid": output_valid,
        "zeroize_flag": zeroize_flag,
        "audit_flag": audit_flag,
        "eagain_flag": eagain_flag,
        "switch_t0_ms": switch_t0,
        "resume_t_ms": resume_t,
        "new_data_t_ms": new_data_t,
        "blackout_ms": new_data_t - switch_t0,
        "flushed_packets": flush_packets,
    }


def render_blackout_jitter(path: Path, results: list[TrialResult], texts: dict[str, object]) -> dict[str, float]:
    blackout_ms = np.array([r.blackout_ms for r in results])
    cpu_load = np.array([r.cpu_load for r in results])
    p50, p95, p99 = np.percentile(blackout_ms, [50, 95, 99])

    img, draw = prepare_canvas()
    left_box = (70, 120, 760, 780)
    right_box = (800, 120, 1450, 780)
    draw_axes(
        draw,
        left_box,
        str(texts["blackout_left_title"]),
        str(texts["blackout_left_xlabel"]),
        str(texts["blackout_left_ylabel"]),
    )
    draw_axes(
        draw,
        right_box,
        str(texts["blackout_right_title"]),
        str(texts["blackout_right_xlabel"]),
        str(texts["blackout_right_ylabel"]),
    )

    xs = np.arange(blackout_ms.size, dtype=np.float64)
    scatter_pts = scale_points(xs, blackout_ms, left_box)
    left_x0, left_y0, left_x1, left_y1 = left_box
    left_left = left_x0 + 80
    left_right = left_x1 - 24
    left_top = left_y0 + 30
    left_bottom = left_y1 - 60

    for (px, py), load in zip(scatter_pts, cpu_load):
        color = color_from_load(float(load))
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color, outline=color)

    min_y = float(blackout_ms.min())
    max_y = float(blackout_ms.max())
    if max_y == min_y:
        max_y = min_y + 1.0
    for label, value, color in (("2 ms", 2.0, RED), ("P95", float(p95), ORANGE), ("P99", float(p99), GOLD)):
        py = left_bottom - (value - min_y) / (max_y - min_y) * (left_bottom - left_top)
        draw.line((left_left, py, left_right, py), fill=color, width=3)
        draw.text((left_right - 120, py - 24), f"{label}={value:.3f}", fill=color, font=get_font(20))

    sorted_ms = np.sort(blackout_ms)
    cdf = (np.arange(sorted_ms.size) + 1.0) / sorted_ms.size
    cdf_pts = scale_points(sorted_ms, cdf, right_box)
    draw.line(cdf_pts, fill=BLUE, width=4)
    for px, py in cdf_pts[:: max(1, len(cdf_pts) // 40)]:
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=BLUE)

    rx0, ry0, rx1, ry1 = right_box
    rleft = rx0 + 80
    rright = rx1 - 24
    rtop = ry0 + 30
    rbottom = ry1 - 60
    xmin = float(sorted_ms.min())
    xmax = float(sorted_ms.max())
    if xmax == xmin:
        xmax = xmin + 1.0
    for label, value, color in (("P50", float(p50), GREEN), ("P95", float(p95), ORANGE), ("P99", float(p99), RED)):
        px = rleft + (value - xmin) / (xmax - xmin) * (rright - rleft)
        draw.line((px, rtop, px, rbottom), fill=color, width=3)
        draw.text((px + 6, rtop + 8), f"{label}={value:.3f}", fill=color, font=get_font(20))

    legend_y = 812
    draw.text((80, legend_y), str(texts["blackout_legend_1"]), fill=FG, font=get_font(20))
    draw.text((80, legend_y + 28), str(texts["blackout_legend_2"]), fill=FG, font=get_font(20))
    img.save(path)

    return {
        "mean_ms": float(blackout_ms.mean()),
        "std_ms": float(blackout_ms.std(ddof=0)),
        "p50_ms": float(p50),
        "p95_ms": float(p95),
        "p99_ms": float(p99),
        "max_ms": float(blackout_ms.max()),
        "min_ms": float(blackout_ms.min()),
    }


def render_timeline(path: Path, timeline: dict[str, np.ndarray | float], texts: dict[str, object]) -> None:
    times = np.asarray(timeline["times_ms"])
    queue = np.asarray(timeline["queue_packets"])
    output_valid = np.asarray(timeline["output_valid"])
    zeroize_flag = np.asarray(timeline["zeroize_flag"])
    audit_flag = np.asarray(timeline["audit_flag"])
    eagain_flag = np.asarray(timeline["eagain_flag"])

    img, draw = prepare_canvas(height=980)

    box1 = (70, 110, 1450, 340)
    box2 = (70, 390, 1450, 620)
    box3 = (70, 670, 1450, 910)

    draw_axes(draw, box1, str(texts["queue_title"]), str(texts["queue_xlabel"]), str(texts["queue_ylabel"]))
    draw_axes(draw, box2, str(texts["state_title"]), str(texts["state_xlabel"]), str(texts["state_ylabel"]))
    draw_axes(draw, box3, str(texts["window_title"]), str(texts["window_xlabel"]), str(texts["window_ylabel"]))

    queue_pts = scale_points(times, queue, box1)
    draw.line(queue_pts, fill=BLUE, width=4)
    for px, py in queue_pts[:: max(1, len(queue_pts) // 60)]:
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=BLUE)

    state_labels = list(texts["state_labels"])
    state_series = [
        (output_valid, 0.55, GREEN, state_labels[0]),
        (eagain_flag, 1.65, ORANGE, state_labels[1]),
        (zeroize_flag, 2.75, RED, state_labels[2]),
        (audit_flag, 3.85, GOLD, state_labels[3]),
    ]

    x0, y0, x1, y1 = box2
    left = x0 + 80
    right = x1 - 24
    top = y0 + 30
    bottom = y1 - 60
    time_min = float(times.min())
    time_max = float(times.max())
    if time_max == time_min:
        time_max = time_min + 1.0
    def map_x(t: float) -> float:
        return left + (t - time_min) / (time_max - time_min) * (right - left)
    def map_y(v: float) -> float:
        y_min, y_max = 0.0, 4.4
        return bottom - (v - y_min) / (y_max - y_min) * (bottom - top)

    for series, level, color, label in state_series:
        pts = [(map_x(float(t)), map_y(level + 0.8 * float(v))) for t, v in zip(times, series)]
        draw.line(pts, fill=color, width=4)
        draw.text((right - 240, map_y(level + 0.72) - 12), label, fill=color, font=get_font(20))

    switch_t0 = float(timeline["switch_t0_ms"])
    resume_t = float(timeline["resume_t_ms"])
    new_data_t = float(timeline["new_data_t_ms"])

    bx0, by0, bx1, by1 = box3
    bleft = bx0 + 80
    bright = bx1 - 24
    btop = by0 + 30
    bbottom = by1 - 60
    blackout_left = bleft + (switch_t0 - time_min) / (time_max - time_min) * (bright - bleft)
    blackout_right = bleft + (new_data_t - time_min) / (time_max - time_min) * (bright - bleft)
    draw.rectangle((blackout_left, btop, blackout_right, bbottom), fill=LIGHT_RED, outline=None)
    availability = np.where(output_valid > 0.5, 1.0, 0.0)
    avail_pts = scale_points(times, availability, box3)
    draw.line(avail_pts, fill=GREY, width=4)
    draw.text((blackout_left + 12, btop + 10), str(texts["blackout_window"]), fill=RED, font=get_font(22))
    draw.line((blackout_left, btop, blackout_left, bbottom), fill=GREY, width=2)
    draw.line((blackout_right, btop, blackout_right, bbottom), fill=GREEN, width=2)
    draw.text((blackout_left - 46, bbottom + 8), f"{switch_t0:.2f}", fill=FG, font=get_font(18))
    draw.text((blackout_right - 30, bbottom + 8), f"{new_data_t:.2f}", fill=FG, font=get_font(18))
    footer = str(texts["timeline_footer"]).format(
        blackout=float(timeline["blackout_ms"]),
        flushed=float(timeline["flushed_packets"]),
    )
    draw.text((80, 932), footer, fill=FG, font=get_font(20))

    img.save(path)


def build_summary(results: list[TrialResult], blackout_stats: dict[str, float], timeline: dict[str, np.ndarray | float]) -> dict[str, object]:
    block = np.array([r.block_io_us for r in results])
    zeroize = np.array([r.zeroize_us for r in results])
    rebuild = np.array([r.rebuild_us for r in results])
    audit = np.array([r.audit_us for r in results])
    resume = np.array([r.resume_us for r in results])
    flushed = np.array([r.flushed_packets for r in results])
    stale = int(sum(r.stale_after_resume for r in results))

    return {
        "simulation_method": "Python 行为级生产者-消费者模型，模拟双设备节点、SG DMA 环形缓冲区、模式切换状态机与 Zeroize 黑障时间。",
        "n_switch_trials": len(results),
        "fast_path_target_gbps": 12.0,
        "cert_path_read_policy": "阻塞式 read + poll，健康状态不满足时返回 -EAGAIN/-EIO，避免无限等待。",
        "blackout_stats_ms": blackout_stats,
        "state_durations_us": {
            "block_io_mean": float(block.mean()),
            "zeroize_mean": float(zeroize.mean()),
            "rebuild_mean": float(rebuild.mean()),
            "audit_mean": float(audit.mean()),
            "resume_mean": float(resume.mean()),
        },
        "queue_integrity": {
            "mean_flushed_packets": float(flushed.mean()),
            "max_flushed_packets": int(flushed.max()),
            "stale_packets_after_resume": stale,
        },
        "representative_timeline": {
            "switch_t0_ms": float(timeline["switch_t0_ms"]),
            "resume_t_ms": float(timeline["resume_t_ms"]),
            "new_data_t_ms": float(timeline["new_data_t_ms"]),
            "blackout_ms": float(timeline["blackout_ms"]),
            "flushed_packets": float(timeline["flushed_packets"]),
        },
    }


def main() -> None:
    args = parse_args()
    fig_dir = resolve_output_dir(args.output_dir)
    summary_path = fig_dir / "chapter4_simulation_summary.json"
    device_fig = fig_dir / "chapter4_driver_stack_architecture.svg"
    state_fig = fig_dir / "chapter4_mode_switch_state_machine.svg"
    blackout_fig = fig_dir / "chapter4_blackout_jitter.png"
    timeline_fig = fig_dir / "chapter4_queue_timeline.png"
    texts = build_text(args.locale)
    ensure_dirs(fig_dir)
    if args.with_svg:
        save_driver_stack_svg(device_fig)
        save_state_machine_svg(state_fig)
    results = simulate_blackout_trials()
    blackout_stats = render_blackout_jitter(blackout_fig, results, texts)
    timeline = simulate_representative_timeline()
    render_timeline(timeline_fig, timeline, texts)
    summary = build_summary(results, blackout_stats, timeline)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
