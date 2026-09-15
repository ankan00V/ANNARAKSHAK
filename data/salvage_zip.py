"""Recover entries from a ZIP whose download lost bytes in the middle.

    .venv/bin/python data/salvage_zip.py ARCHIVE.zip OUT_DIR PREFIX [PREFIX ...]

Browsers sometimes drop a chunk of a multi-GB download while keeping the end of
the file, so unzip/zipfile refuse it ("corrupt zip64 end of central directory")
even though almost every entry is intact. The central directory at the end
still lists every file with its size and CRC-32; entries after a gap simply sit
earlier in the file than recorded. For each wanted entry this finds its local
header (at the recorded offset, or shifted back by the gap), inflates it and
keeps it only if the CRC matches — an entry that straddles the gap fails the
CRC and is reported, never written half-broken.
"""

from __future__ import annotations

import os
import struct
import sys
import zlib
from pathlib import Path


def central_directory(f, size: int) -> tuple[list[dict], int, int]:
    f.seek(max(0, size - 65536))
    base = f.tell()
    tail = f.read()
    z64 = tail.rfind(b"PK\x06\x06")
    if z64 < 0:
        raise SystemExit("no ZIP64 end record — this tool is for large ZIP64 archives")
    (_, _, _, _, _, _, _, n_total, cd_size, cd_off) = struct.unpack("<IQHHIIQQQQ", tail[z64:z64 + 56])
    actual_cd = base + z64 - cd_size
    shift = cd_off - actual_cd  # bytes missing before the central directory
    f.seek(actual_cd)
    cd = f.read(cd_size)
    entries, i = [], 0
    while i < len(cd) and cd[i:i + 4] == b"PK\x01\x02":
        flag, method = struct.unpack("<HH", cd[i + 8:i + 12])
        crc, csize, usize = struct.unpack("<III", cd[i + 16:i + 28])
        nl, el, cl = struct.unpack("<HHH", cd[i + 28:i + 34])
        off, = struct.unpack("<I", cd[i + 42:i + 46])
        name = cd[i + 46:i + 46 + nl].decode("utf-8", "replace")
        extra = cd[i + 46 + nl:i + 46 + nl + el]
        j = 0  # ZIP64 extra field carries the real sizes/offset when the 32-bit ones are 0xFFFFFFFF
        while j + 4 <= len(extra):
            hid, hlen = struct.unpack("<HH", extra[j:j + 4])
            data = extra[j + 4:j + 4 + hlen]
            if hid == 0x0001:
                k = 0
                if usize == 0xFFFFFFFF:
                    usize, = struct.unpack("<Q", data[k:k + 8]); k += 8
                if csize == 0xFFFFFFFF:
                    csize, = struct.unpack("<Q", data[k:k + 8]); k += 8
                if off == 0xFFFFFFFF:
                    off, = struct.unpack("<Q", data[k:k + 8]); k += 8
            j += 4 + hlen
        entries.append({"name": name, "flag": flag, "method": method, "crc": crc, "csize": csize, "usize": usize, "off": off})
        i += 46 + nl + el + cl
    if len(entries) != n_total:
        print(f"warning: parsed {len(entries)} of {n_total} directory entries")
    return entries, shift, actual_cd


def read_entry(f, e: dict, shift: int) -> bytes | None:
    for off in (e["off"], e["off"] - shift):
        if off < 0:
            continue
        f.seek(off)
        h = f.read(30)
        if len(h) < 30 or h[:4] != b"PK\x03\x04":
            continue
        nl, el = struct.unpack("<HH", h[26:30])
        if f.read(nl).decode("utf-8", "replace") != e["name"]:
            continue
        f.seek(el, os.SEEK_CUR)
        raw = f.read(e["csize"])
        try:
            data = zlib.decompress(raw, -15) if e["method"] == 8 else raw
        except zlib.error:
            continue
        if zlib.crc32(data) & 0xFFFFFFFF == e["crc"] and len(data) == e["usize"]:
            return data
    return None


def locate_all(f, size: int, by_name: dict[str, dict], cd_start: int) -> dict[str, int]:
    """Walk the local headers from the start; after a gap (no header where the
    previous entry ended), scan forward to the next header whose name is in the
    directory. Handles any number of gaps, each with its own shift."""
    where: dict[str, int] = {}
    pos, resyncs, CH = 0, 0, 1 << 24
    while pos < cd_start:
        f.seek(pos)
        h = f.read(30)
        e = None
        if h[:4] == b"PK\x03\x04":
            nl, el = struct.unpack("<HH", h[26:30])
            name = f.read(nl).decode("utf-8", "replace")
            e = by_name.get(name)
        if e is not None:
            where[e["name"]] = pos
            pos += 30 + nl + el + e["csize"]
            if e.get("flag", 0) & 0x08:  # data descriptor follows the data
                f.seek(pos)
                dd = f.read(24)
                pos += (4 if dd[:4] == b"PK\x07\x08" else 0) + (20 if e["csize"] > 0xFFFFFFFE else 12)
            continue
        # lost sync: find the next plausible local header
        resyncs += 1
        start = pos + 1
        found = None
        while found is None and start < cd_start:
            f.seek(start)
            buf = f.read(CH + 64)
            k = buf.find(b"PK\x03\x04")
            while k >= 0 and k + 30 <= len(buf):
                nl = struct.unpack("<H", buf[k + 26:k + 28])[0]
                name = buf[k + 30:k + 30 + nl].decode("utf-8", "replace")
                if name in by_name:
                    found = start + k
                    break
                k = buf.find(b"PK\x03\x04", k + 1)
            start += CH
        if found is None:
            break
        pos = found
    print(f"  walked local headers: {len(where)} located, {resyncs} resyncs across gaps")
    return where


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    archive, out, prefixes = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    size = archive.stat().st_size
    ok = bad = 0
    lost: list[str] = []
    with archive.open("rb") as f:
        entries, shift, cd_start = central_directory(f, size)
        print(f"{archive.name}: {len(entries)} entries, {shift:,} bytes missing")
        by_name = {e["name"]: e for e in entries}
        where = locate_all(f, size, by_name, cd_start)
        for e in entries:
            if e["name"].endswith("/") or not any(e["name"].startswith(p) for p in prefixes):
                continue
            dest = out / e["name"]
            if dest.exists() and dest.stat().st_size == e["usize"]:
                ok += 1
                continue
            data = read_entry(f, e | {"off": where.get(e["name"], e["off"])}, shift)
            if data is None:
                bad += 1
                lost.append(e["name"])
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            ok += 1
    print(f"recovered {ok}, lost {bad} (CRC mismatch or inside the missing bytes)")
    if lost:
        (out / f"{archive.stem}_LOST.txt").write_text("\n".join(lost) + "\n")
        print(f"lost entries listed in {out / (archive.stem + '_LOST.txt')}")


if __name__ == "__main__":
    main()
