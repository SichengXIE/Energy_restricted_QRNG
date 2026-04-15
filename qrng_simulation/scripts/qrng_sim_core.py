from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np


TRACK_A_BLOCK_IN_BITS = 1024
TRACK_A_BLOCK_OUT_BITS = 256
TRACK_B_BLOCK_RAW_BITS = 512
TRACK_B_BLOCK_OUT_BITS = 512


def generate_one_over_f_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    freqs = np.fft.rfftfreq(n)
    spectrum = rng.normal(size=freqs.size) + 1j * rng.normal(size=freqs.size)
    scale = np.ones_like(freqs)
    nonzero = freqs > 0
    scale[nonzero] = 1.0 / np.sqrt(freqs[nonzero])
    spectrum *= scale
    noise = np.fft.irfft(spectrum, n=n)
    std = max(float(noise.std()), 1e-12)
    return (noise - noise.mean()) / std


def quantize_samples(samples: np.ndarray, bits: int = 12, clip_sigma: float = 6.0) -> np.ndarray:
    sigma = max(float(np.std(samples)), 1e-12)
    clip = clip_sigma * sigma
    levels = 2**bits
    clipped = np.clip(samples, -clip, clip)
    scaled = (clipped + clip) / (2.0 * clip)
    return np.floor(scaled * (levels - 1)).astype(np.uint16)


def uints_to_bits(values: np.ndarray, bit_width: int) -> np.ndarray:
    shifts = np.arange(bit_width, dtype=np.uint16)
    bits = ((values[:, None] >> shifts) & 1).astype(np.uint8)
    return bits.reshape(-1)


def dense_linear_extract(raw_bits: np.ndarray, out_bits: int, rng: np.random.Generator) -> np.ndarray:
    matrix = rng.integers(0, 2, size=(out_bits, raw_bits.size), dtype=np.int16)
    products = matrix @ raw_bits.astype(np.int16)
    return (products & 1).astype(np.uint8)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    if bits.size == 0:
        return b""
    if bits.size % 8:
        bits = np.pad(bits, (0, 8 - bits.size % 8), constant_values=0)
    return np.packbits(bits, bitorder="little").tobytes()


def bytes_to_bits(data: bytes) -> np.ndarray:
    if not data:
        return np.zeros(0, dtype=np.uint8)
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")


def generate_track_a_raw_bits(
    rng: np.random.Generator,
    n_bits: int,
    cmrr_db: float = 40.0,
    adc_bits: int = 12,
) -> np.ndarray:
    n_samples = int(math.ceil(n_bits / adc_bits))
    sigma_q = max(0.70, 1.0 - 5.0 * 10 ** (-cmrr_db / 20.0))
    thermal_sigma = 0.22
    onef_sigma = 0.10
    leakage_sigma = 0.60 * 10 ** (-(cmrr_db - 30.0) / 20.0)

    quantum = rng.normal(0.0, sigma_q, n_samples)
    thermal = rng.normal(0.0, thermal_sigma, n_samples)
    one_f = generate_one_over_f_noise(n_samples, rng) * onef_sigma
    lo_drift = generate_one_over_f_noise(n_samples, rng) * leakage_sigma
    adc = rng.uniform(-0.015, 0.015, n_samples)
    samples = quantum + thermal + one_f + lo_drift + adc
    quantized = quantize_samples(samples, bits=adc_bits)
    return uints_to_bits(quantized, adc_bits)[:n_bits]


def generate_track_a_bits(
    rng: np.random.Generator,
    out_bits: int,
    cmrr_db: float = 40.0,
    conditioned: bool = True,
) -> np.ndarray:
    if not conditioned:
        return generate_track_a_raw_bits(rng, out_bits, cmrr_db=cmrr_db)

    blocks: list[np.ndarray] = []
    blocks_needed = int(math.ceil(out_bits / TRACK_A_BLOCK_OUT_BITS))
    for _ in range(blocks_needed):
        raw_bits = generate_track_a_raw_bits(rng, TRACK_A_BLOCK_IN_BITS, cmrr_db=cmrr_db)
        blocks.append(dense_linear_extract(raw_bits, TRACK_A_BLOCK_OUT_BITS, rng))
    return np.concatenate(blocks)[:out_bits]


def generate_track_b_raw_block(
    rng: np.random.Generator,
    block_bits: int = TRACK_B_BLOCK_RAW_BITS,
    n_channels: int = 8,
) -> np.ndarray:
    bits_per_channel = block_bits // n_channels
    channels = []
    shared = rng.normal(0.0, 0.010, bits_per_channel)
    for ch in range(n_channels):
        increments = rng.normal(0.0, 0.60 + 0.015 * ch, bits_per_channel) + shared
        phase = np.cumsum(increments)
        analog = np.cos(phase) + rng.normal(0.0, 0.04, bits_per_channel)
        raw = (analog > 0.0).astype(np.uint8)
        whitened = np.bitwise_xor(raw[1:], raw[:-1]).astype(np.uint8)
        padded = np.pad(whitened, (0, bits_per_channel - whitened.size), constant_values=0)
        channels.append(padded)
    return np.concatenate(channels)


def shake256_expand(seed: bytes, raw_bits: np.ndarray, out_bytes: int = 64) -> bytes:
    raw_bytes = bits_to_bytes(raw_bits)
    return hashlib.shake_256(seed + raw_bytes).digest(out_bytes)


def generate_track_b_bits(
    rng: np.random.Generator,
    out_bits: int,
    conditioned: bool = True,
) -> np.ndarray:
    if not conditioned:
        blocks_needed = int(math.ceil(out_bits / TRACK_B_BLOCK_RAW_BITS))
        blocks = [generate_track_b_raw_block(rng) for _ in range(blocks_needed)]
        return np.concatenate(blocks)[:out_bits]

    seed = rng.bytes(32)
    blocks: list[np.ndarray] = []
    blocks_needed = int(math.ceil(out_bits / TRACK_B_BLOCK_OUT_BITS))
    for block_idx in range(blocks_needed):
        if block_idx % 128 == 0:
            seed = hashlib.sha3_256(seed + rng.bytes(32)).digest()
        raw_block = generate_track_b_raw_block(rng)
        mixed = shake256_expand(seed, raw_block, out_bytes=TRACK_B_BLOCK_OUT_BITS // 8)
        blocks.append(bytes_to_bits(mixed))
    return np.concatenate(blocks)[:out_bits]


def generate_track_bits(
    track: str,
    out_bits: int,
    seed: int,
    conditioned: bool = True,
    cmrr_db: float = 40.0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if track == "a":
        return generate_track_a_bits(rng, out_bits, cmrr_db=cmrr_db, conditioned=conditioned)
    if track == "b":
        return generate_track_b_bits(rng, out_bits, conditioned=conditioned)
    raise ValueError(f"Unsupported track: {track}")


def lag1_correlation(bits: np.ndarray) -> float:
    if bits.size < 2:
        return 0.0
    signed = 2.0 * bits.astype(np.float64) - 1.0
    return float(np.dot(signed[:-1], signed[1:]) / (signed.size - 1))


def byte_histogram(data: bytes) -> np.ndarray:
    if not data:
        return np.zeros(256, dtype=np.int64)
    return np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)


def quick_self_check(bits: np.ndarray) -> dict[str, float | int]:
    if bits.size == 0:
        return {
            "bit_count": 0,
            "byte_count": 0,
            "ones_ratio": 0.0,
            "bit_bias": 0.0,
            "runs": 0,
            "expected_runs": 0.0,
            "lag1_correlation": 0.0,
            "byte_entropy_bits": 0.0,
            "byte_min_entropy_bits": 0.0,
        }

    ones = int(bits.sum())
    runs = int(1 + np.count_nonzero(bits[1:] != bits[:-1]))
    pi = ones / bits.size
    expected_runs = 1.0 + 2.0 * max(bits.size - 1, 0) * pi * (1.0 - pi)

    data = bits_to_bytes(bits)
    counts = byte_histogram(data).astype(np.float64)
    probs = counts / max(counts.sum(), 1.0)
    nz = probs[probs > 0]
    byte_entropy = float(-(nz * np.log2(nz)).sum()) if nz.size else 0.0
    byte_min_entropy = float(-math.log2(max(float(probs.max()), 1e-12)))

    return {
        "bit_count": int(bits.size),
        "byte_count": len(data),
        "ones_ratio": float(pi),
        "bit_bias": float(abs(pi - 0.5)),
        "runs": runs,
        "expected_runs": float(expected_runs),
        "lag1_correlation": lag1_correlation(bits),
        "byte_entropy_bits": byte_entropy,
        "byte_min_entropy_bits": byte_min_entropy,
    }


def preview_values(data: bytes, fmt: str, show: int) -> list[str]:
    if fmt == "bits":
        bits = bytes_to_bits(data)
        groups = []
        for idx in range(show):
            start = idx * 32
            stop = start + 32
            if start >= bits.size:
                break
            groups.append("".join(str(int(x)) for x in bits[start:stop]))
        return groups

    if fmt == "u32":
        padded = data + (b"\x00" * ((4 - len(data) % 4) % 4))
        values = np.frombuffer(padded, dtype="<u4")
        return [str(int(x)) for x in values[:show]]

    chunk_width = 16
    return [data[idx * chunk_width:(idx + 1) * chunk_width].hex() for idx in range(show) if idx * chunk_width < len(data)]


def save_binary_output(output_dir: Path, track: str, data: bytes) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"track_{track}.bin"
    path.write_bytes(data)
    return path
