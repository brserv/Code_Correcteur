"""Serial framing and simple send/receive with resynchronization.

Frame format: STX(0x02) | LEN(2 bytes, big endian) | PAYLOAD | ETX(0x03)

This module provides helper functions to build frames, parse buffers and a
`SerialLink` helper to send a frame and wait for a returned frame (suitable for loopback tests).
"""
from typing import List, Tuple, Optional
import serial
import time
from serial.tools import list_ports

STX = 0x02
ETX = 0x03


def list_serial_ports() -> List[str]:
    return [p.device for p in list_ports.comports()]


def build_frame(payload: bytes) -> bytes:
    L = len(payload)
    return bytes([STX]) + L.to_bytes(2, 'big') + payload + bytes([ETX])


def parse_frames(buffer: bytearray) -> List[Tuple[int, int, bytes]]:
    """Scan buffer for complete frames.

    Returns list of tuples (start_index, end_index_exclusive, payload_bytes).
    """
    frames = []
    i = 0
    b = buffer
    while True:
        try:
            st = b.index(STX, i)
        except ValueError:
            break
        if st + 3 > len(b):
            break
        L = int.from_bytes(b[st + 1:st + 3], 'big')
        end_idx = st + 3 + L
        if end_idx + 1 > len(b):
            break
        if b[end_idx] == ETX:
            payload = bytes(b[st + 3:end_idx])
            frames.append((st, end_idx + 1, payload))
            i = end_idx + 1
        else:
            i = st + 1
    return frames


class SerialLink:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    def open(self):
        if self.ser and self.ser.is_open:
            return
        self.ser = serial.Serial(self.port, self.baud, bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 timeout=self.timeout)

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_and_receive(self, frame: bytes, read_timeout: float = 1.0) -> Tuple[Optional[bytes], bytes]:
        """Send a frame and wait for a returned frame (loopback). Returns (payload, leftover_buffer_bytes).

        If no frame received within timeout returns (None, leftover_bytes).
        """
        if not self.ser or not self.ser.is_open:
            self.open()
        # clear input buffer
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self.ser.write(frame)
        self.ser.flush()
        t0 = time.time()
        buf = bytearray()
        while time.time() - t0 < read_timeout:
            b = self.ser.read(1)
            if b:
                buf.extend(b)
                frames = parse_frames(buf)
                if frames:
                    st, end, payload = frames[0]
                    # consume
                    del buf[:end]
                    return payload, bytes(buf)
        return None, bytes(buf)
