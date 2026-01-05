"""Codec wrapper using Reed-Solomon (per-octet correction).

Provides ChannelCodec which encodes/decodes payloads. nsym = 2*t parity bytes (can correct up to t byte-errors).
"""
from typing import Tuple
from reedsolo import RSCodec, ReedSolomonError


class ChannelCodec:
    def __init__(self, t: int = 2, enabled: bool = True):
        self.t = int(t)
        self.nsym = 2 * self.t
        self.enabled = bool(enabled)
        if self.enabled:
            self.rs = RSCodec(self.nsym)
        else:
            self.rs = None

    def encode(self, data: bytes) -> bytes:
        if not self.enabled:
            return data
        return bytes(self.rs.encode(data))

    def decode(self, data: bytes) -> Tuple[bytes, str, bool, int]:
        """Decode data. Returns (decoded_bytes, status_str, success_flag, num_errors_corrected).

        status_str can be: 'corrected', 'ok', 'error:<msg>' or 'raw' when disabled.
        """
        if not self.enabled:
            return data, 'raw', True, 0
        try:
            decoded, _, error_positions = self.rs.decode(data)
            num_errors = len(error_positions) if error_positions else 0
            status = 'corrected' if num_errors > 0 else 'ok'
            return bytes(decoded), status, True, num_errors
        except ReedSolomonError as e:
            return b'', f'error:{e}', False, 0
        except Exception as e:
            return b'', f'error:{e}', False, 0
