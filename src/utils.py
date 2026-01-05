"""Utility helpers: error injection and hex formatting."""
import random
from typing import Tuple


def to_hex(b: bytes) -> str:
    return ' '.join(f'{x:02X}' for x in b)


def to_bin(b: bytes) -> str:
    return ' '.join(f'{x:08b}' for x in b)


def to_text(b: bytes) -> str:
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return '<Non-UTF8>'


def flip_bit_in_byte(value: int, bit: int) -> int:
    return value ^ (1 << bit)


def inject_manual(payload: bytes, index: int, bit: int) -> bytes:
    arr = bytearray(payload)
    if 0 <= index < len(arr) and 0 <= bit < 8:
        arr[index] = flip_bit_in_byte(arr[index], bit)
    return bytes(arr)


def inject_random(payload: bytes, n_bytes: int = 1, bits_per_byte: int = 1, seed: int | None = None) -> Tuple[bytes, int]:
    """Flip random bits in random bytes. Returns (new_payload, injected_count_bits).
    n_bytes = number of distinct bytes to corrupt, bits_per_byte = how many bits per selected byte to flip.
    """
    if seed is not None:
        random.seed(seed)
    arr = bytearray(payload)
    L = len(arr)
    if L == 0 or n_bytes <= 0:
        return bytes(arr), 0
    indexes = random.sample(range(L), min(n_bytes, L))
    total_flips = 0
    for idx in indexes:
        for _ in range(bits_per_byte):
            bit = random.randrange(0, 8)
            arr[idx] ^= (1 << bit)
            total_flips += 1
    return bytes(arr), total_flips


def inject_exact_bits(payload: bytes, num_bits: int, seed: int | None = None) -> bytes:
    """Flip exactly num_bits random bits in the payload."""
    if seed is not None:
        random.seed(seed)
    arr = bytearray(payload)
    L = len(arr)
    if L == 0 or num_bits <= 0:
        return bytes(arr)
    total_bits = L * 8
    if num_bits > total_bits:
        num_bits = total_bits
    # Select num_bits unique positions
    positions = random.sample(range(total_bits), num_bits)
    for pos in positions:
        byte_idx = pos // 8
        bit_idx = pos % 8
        arr[byte_idx] ^= (1 << bit_idx)
    return bytes(arr)
