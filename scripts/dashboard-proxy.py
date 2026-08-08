#!/usr/bin/env python3
"""Async reverse proxy: 0.0.0.0:9120 -> 127.0.0.1:9122
Rewrites Host header to 127.0.0.1 so dashboard (bound to loopback, no auth)
accepts requests with any Host header (hermes.jefe.al, etc.).
Handles HTTP and WebSocket upgrades via raw TCP piping."""

import asyncio
import sys
import datetime

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 9121
TARGET_HOST = "127.0.0.1"
TARGET_PORT = 9120


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def handle_client(reader, writer):
    try:
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = await reader.read(4096)
            if not chunk:
                writer.close()
                return
            header_data += chunk
            if len(header_data) > 65536:
                break

        lines = header_data.split(b"\r\n")
        new_lines = []
        for line in lines:
            if line.lower().startswith(b"host:"):
                new_lines.append(f"Host: {TARGET_HOST}:{TARGET_PORT}".encode())
            else:
                new_lines.append(line)
        rewritten = b"\r\n".join(new_lines)

        header_end = rewritten.find(b"\r\n\r\n")
        if header_end != -1:
            header_part = rewritten[:header_end + 4]
            body_part = rewritten[header_end + 4:]
        else:
            header_part = rewritten
            body_part = b""

        try:
            dash_reader, dash_writer = await asyncio.open_connection(TARGET_HOST, TARGET_PORT)
        except ConnectionRefusedError:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()
            return

        dash_writer.write(header_part)
        if body_part:
            dash_writer.write(body_part)
        await dash_writer.drain()

        task1 = asyncio.create_task(pipe(reader, dash_writer))
        task2 = asyncio.create_task(pipe(dash_reader, writer))
        await asyncio.gather(task1, task2, return_exceptions=True)

    except Exception as e:
        try:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()
        except:
            pass


async def main():
    server = await asyncio.start_server(handle_client, LISTEN_HOST, LISTEN_PORT)
    log(f"Proxy {LISTEN_HOST}:{LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())