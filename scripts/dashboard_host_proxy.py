#!/usr/bin/env python3
"""Loopback-only TCP proxy that normalizes Host for the Hermes dashboard.

Pangolin reaches this proxy on 127.0.0.1:8999.  The proxy forwards to the
loopback-only dashboard on 127.0.0.1:9119, replacing only the first HTTP Host
header.  It then transparently relays the byte stream, including WebSockets.
"""

import asyncio
import contextlib

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8999
UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 9119
MAX_HEADER_BYTES = 64 * 1024


def normalize_host_header(head: bytes) -> bytes:
    lines = head.split(b"\r\n")
    changed = False
    for index, line in enumerate(lines):
        if line.lower().startswith(b"host:"):
            lines[index] = b"Host: 127.0.0.1:9119"
            changed = True
            break
    if not changed:
        raise ValueError("missing Host header")
    return b"\r\n".join(lines)


async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while chunk := await reader.read(64 * 1024):
            writer.write(chunk)
            await writer.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        with contextlib.suppress(Exception):
            writer.close()
            await writer.wait_closed()


async def handle(client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
    try:
        header = await asyncio.wait_for(client_reader.readuntil(b"\r\n\r\n"), timeout=15)
        if len(header) > MAX_HEADER_BYTES:
            raise ValueError("headers too large")
        upstream_reader, upstream_writer = await asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT)
        upstream_writer.write(normalize_host_header(header))
        await upstream_writer.drain()
        await asyncio.gather(
            relay(client_reader, upstream_writer),
            relay(upstream_reader, client_writer),
        )
    except Exception:
        with contextlib.suppress(Exception):
            client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
            await client_writer.drain()
        with contextlib.suppress(Exception):
            client_writer.close()
            await client_writer.wait_closed()


async def main() -> None:
    server = await asyncio.start_server(handle, LISTEN_HOST, LISTEN_PORT)
    print(f"HOST_PROXY_READY {LISTEN_HOST}:{LISTEN_PORT} -> {UPSTREAM_HOST}:{UPSTREAM_PORT}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
