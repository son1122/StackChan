#!/usr/bin/env python3
"""
Utility script to find the first bindable TCP port on the host.
Scans preferred high ports before scanning dynamically.
"""
import socket
import sys

def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False

def get_free_port() -> int:
    candidates = [8099, 8383, 8765, 18080, 28080, 38080]
    for p in candidates:
        if is_port_available(p):
            return p
    p = 18080
    while not is_port_available(p):
        p += 1
    return p

if __name__ == "__main__":
    print(get_free_port())
