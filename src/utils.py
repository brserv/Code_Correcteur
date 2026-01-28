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


def inject_errors_per_byte(payload: bytes, errors_per_byte: int, seed: int | None = None) -> bytes:
    """Inject errors_per_byte random bit-flips in each byte of the payload.
    
    For example, with errors_per_byte=2, each byte will have 2 random bits flipped.
    """
    if seed is not None:
        random.seed(seed)
    arr = bytearray(payload)
    L = len(arr)
    if L == 0 or errors_per_byte <= 0:
        return bytes(arr)
    
    total_flips = 0
    for byte_idx in range(L):
        # For each byte, flip errors_per_byte random bits
        flips_in_byte = min(errors_per_byte, 8)
        bit_positions = random.sample(range(8), flips_in_byte)
        for bit_idx in bit_positions:
            arr[byte_idx] ^= (1 << bit_idx)
            total_flips += 1
    
    return bytes(arr)


def inject_errors_in_byte(payload: bytes, byte_index: int, num_errors: int, seed: int | None = None) -> bytes:
    """Inject num_errors random bit-flips in a specific byte of the payload.
    
    For example, with byte_index=2 and num_errors=3, byte at index 2 will have 3 random bits flipped.
    """
    if seed is not None:
        random.seed(seed)
    arr = bytearray(payload)
    L = len(arr)
    
    if L == 0 or num_errors <= 0 or byte_index < 0 or byte_index >= L:
        return bytes(arr)
    
    # Flip num_errors random bits in the specified byte
    flips_in_byte = min(num_errors, 8)
    bit_positions = random.sample(range(8), flips_in_byte)
    for bit_idx in bit_positions:
        arr[byte_index] ^= (1 << bit_idx)
    
    return bytes(arr)


def inject_errors_in_n_bytes(payload: bytes, n_bytes: int, errors_per_byte: int, seed: int | None = None) -> bytes:
    """Inject errors_per_byte random bit-flips in n_bytes random bytes of the payload.
    
    For example, with n_bytes=3 and errors_per_byte=2, 3 random bytes will each have 2 bits flipped.
    """
    if seed is not None:
        random.seed(seed)
    arr = bytearray(payload)
    L = len(arr)
    
    if L == 0 or n_bytes <= 0 or errors_per_byte <= 0:
        return bytes(arr)
    
    # Select n_bytes random indices to corrupt
    num_bytes_to_corrupt = min(n_bytes, L)
    byte_indices = random.sample(range(L), num_bytes_to_corrupt)
    
    # Inject errors_per_byte in each selected byte
    for byte_idx in byte_indices:
        flips_in_byte = min(errors_per_byte, 8)
        bit_positions = random.sample(range(8), flips_in_byte)
        for bit_idx in bit_positions:
            arr[byte_idx] ^= (1 << bit_idx)
    
    return bytes(arr)
