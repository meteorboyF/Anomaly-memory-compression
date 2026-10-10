"""Download, verify, persist, and stage the MVTec AD archive.

Flow (idempotent; every step is skipped when its verified marker matches):

1. Drive archive with a verified marker?  -> reuse it.
   Drive archive WITHOUT a marker (manual upload)?  -> verify it, then mark.
   Neither?  -> resolve the official link from the publisher's downloads page,
   check headers (reject HTML/error pages), check free space, stream to local
   disk with HTTP Range resume and bounded retries.
2. Verify locally: XZ magic bytes, size vs Content-Length, SHA-256 (ours;
   compared with a publisher checksum only if the publisher provides one),
   and a full single-pass safe extraction (no absolute paths, no '..', no
   links or devices) followed by a structure/pairing scan.
3. Copy the archive atomically to Drive, re-hash the Drive copy, then write
   the Drive marker. Markers are written only after verification.
4. Leave the verified extraction on local disk with its own marker.

The dataset is never committed to Git and never duplicated unpacked on Drive.
"""

from __future__ import annotations

import dataclasses
import http.client
import os
import re
import shutil
import socket
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from ..io_utils import (atomic_copy, atomic_write_json, free_bytes, human_bytes, read_json,
                        sha256_file)
from ..manifest import utcnow
from . import mvtec

XZ_MAGIC = b"\xfd7zXZ\x00"
USER_AGENT = "anomaly-memory-acquire/0.1 (+https://github.com/meteorboyF/Anomaly-memory-compression)"
NO_RETRY_MARK = "[no-retry] "


class AcquireError(RuntimeError):
    pass


class NotAnArchive(AcquireError):
    pass


@dataclasses.dataclass
class Plan:
    archive_name: str
    downloads_page: str
    fallback_url: str
    expected_bytes: int | None
    extracted_bytes_estimate: int
    publisher_sha256: str | None
    publisher_md5: str | None
    drive_archive_dir: Path
    local_root: Path
    extracted_dirname: str
    categories: list[str]
    expected_counts: dict | None
    max_retries: int = 5
    timeout_s: float = 60.0
    backoff_s: float = 5.0
    margin_bytes: int = 1 << 30

    @property
    def drive_archive(self) -> Path:
        return self.drive_archive_dir / self.archive_name

    @property
    def drive_marker(self) -> Path:
        return self.drive_archive_dir / f"{self.archive_name}.verified.json"

    @property
    def local_archive(self) -> Path:
        return self.local_root / "archives" / self.archive_name

    @property
    def extract_dir(self) -> Path:
        return self.local_root / "data" / self.extracted_dirname

    @property
    def extract_marker(self) -> Path:
        return self.local_root / "data" / f"{self.extracted_dirname}.extracted.json"


Log = Callable[[str], None]


# ----------------------------------------------------------------------------- HTTP

def _request(url: str, method: str = "GET", headers: dict | None = None, timeout: float = 60.0):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def resolve_url(plan: Plan, log: Log) -> tuple[str, str]:
    """Find the archive link on the official downloads page; fall back to the
    recorded URL only if the page cannot be parsed, and say so."""
    try:
        with _request(plan.downloads_page, timeout=plan.timeout_s) as r:
            html = r.read(4 << 20).decode("utf-8", "replace")
    except (urllib.error.URLError, socket.timeout, http.client.HTTPException) as e:
        log(f"WARNING: could not fetch downloads page ({e}); using recorded URL")
        return plan.fallback_url, "fallback_recorded_url"
    pat = re.compile(r'href="([^"]+/' + re.escape(plan.archive_name) + r')"')
    links = sorted(set(urllib.parse.urljoin(plan.downloads_page, m) for m in pat.findall(html)))
    if len(links) == 1:
        if links[0] != plan.fallback_url:
            log(f"NOTE: official link differs from the recorded one; using the page's link {links[0]}")
        return links[0], "downloads_page"
    if len(links) > 1:
        raise AcquireError(f"ambiguous: {len(links)} links for {plan.archive_name} on {plan.downloads_page}")
    log("WARNING: archive link not found on the downloads page; using recorded URL")
    return plan.fallback_url, "fallback_recorded_url"


def probe(url: str, timeout: float) -> dict:
    """HEAD (or 1-byte GET) to read size/type without downloading."""
    try:
        with _request(url, method="HEAD", timeout=timeout) as r:
            h = dict(r.headers.items())
    except urllib.error.HTTPError as e:
        if e.code not in (403, 405):
            raise
        with _request(url, headers={"Range": "bytes=0-0"}, timeout=timeout) as r:
            h = dict(r.headers.items())
    h = {k.lower(): v for k, v in h.items()}
    ctype = h.get("content-type", "")
    if "text/html" in ctype or "application/json" in ctype:
        raise NotAnArchive(f"server returned {ctype!r} for the archive URL (likely an error/login page)")
    size = None
    if "content-range" in h and "/" in h["content-range"]:
        size = int(h["content-range"].rsplit("/", 1)[1])
    elif "content-length" in h:
        size = int(h["content-length"])
    return {"content_type": ctype, "bytes": size, "etag": h.get("etag"),
            "last_modified": h.get("last-modified"), "accept_ranges": h.get("accept-ranges")}


def stream_download(url: str, dest: Path, expected_bytes: int | None, *, max_retries: int,
                    timeout: float, backoff_s: float, log: Log) -> int:
    """Stream ``url`` to ``dest`` (a .part file) with Range resume and bounded retries."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        have = dest.stat().st_size if dest.exists() else 0
        if expected_bytes is not None and have == expected_bytes:
            return have
        if expected_bytes is not None and have > expected_bytes:
            log(f"partial file larger than expected ({have} > {expected_bytes}); restarting")
            dest.unlink()
            have = 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with _request(url, headers=headers, timeout=timeout) as r:
                ctype = r.headers.get("Content-Type", "")
                if "text/html" in ctype:
                    raise NotAnArchive(f"{NO_RETRY_MARK}server sent HTML ({ctype}) instead of the archive")
                if have and r.status == 200:
                    log("server ignored the Range request; restarting from byte 0")
                    have = 0
                mode = "ab" if have else "wb"
                with open(dest, mode) as f:
                    first = not have
                    done = have
                    next_report = (done // (512 << 20) + 1) * (512 << 20)
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        if first:
                            if not chunk.startswith(XZ_MAGIC):
                                raise NotAnArchive(f"{NO_RETRY_MARK}downloaded bytes are not XZ "
                                                   f"(starts with {chunk[:16]!r})")
                            first = False
                        f.write(chunk)
                        done += len(chunk)
                        if done >= next_report:
                            tot = f" / {human_bytes(expected_bytes)}" if expected_bytes else ""
                            log(f"  downloaded {human_bytes(done)}{tot}")
                            next_report += 512 << 20
            size = dest.stat().st_size
            if expected_bytes is None or size == expected_bytes:
                return size
            last_err = AcquireError(f"short read: {size} of {expected_bytes} bytes")
        except NotAnArchive:
            if dest.exists():
                dest.unlink()
            raise
        except urllib.error.HTTPError as e:
            if e.code == 416 and expected_bytes is not None and have == expected_bytes:
                return have
            if 400 <= e.code < 500 and e.code not in (408, 429):
                raise AcquireError(f"{NO_RETRY_MARK}HTTP {e.code} from server: {e.reason}") from e
            last_err = e
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError,
                http.client.HTTPException) as e:
            last_err = e
        wait = min(backoff_s * 2 ** (attempt - 1), 120)
        log(f"attempt {attempt}/{max_retries} failed ({last_err}); retrying in {wait:.0f}s (resume supported)")
        time.sleep(wait)
    raise AcquireError(f"download failed after {max_retries} attempts: {last_err}")


# ----------------------------------------------------------------------------- archive checks

def check_magic(path: Path) -> None:
    with open(path, "rb") as f:
        head = f.read(64)
    if not head.startswith(XZ_MAGIC):
        kind = "HTML/text" if head.lstrip()[:1] in (b"<", b"{") else "unknown"
        raise NotAnArchive(f"{path.name} is not an XZ archive ({kind} content: {head[:32]!r})")


def _safe_member_path(name: str) -> Path:
    p = Path(name)
    unsafe = (p.is_absolute() or name.startswith(("/", "\\")) or "\\" in name or ".." in p.parts
              or (bool(p.parts) and ":" in p.parts[0]))
    if unsafe:
        raise AcquireError(f"unsafe path in archive: {name!r}")
    return p


def safe_extract(archive: Path, dest: Path, log: Log) -> dict:
    """Single streaming pass: validate every member and extract regular files.

    Refuses absolute paths, '..' components, links, and special files. Returns
    member statistics. ``dest`` must not already exist.
    """
    if dest.exists():
        raise AcquireError(f"extraction target already exists: {dest}")
    dest.mkdir(parents=True)
    n_files = n_bytes = 0
    tops = set()
    with tarfile.open(archive, mode="r|xz") as tf:
        for m in tf:
            rel = _safe_member_path(m.name)
            if not rel.parts:
                continue
            tops.add(rel.parts[0])
            target = dest / rel
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                if src is None:
                    raise AcquireError(f"cannot read member {m.name}")
                with open(target, "wb") as out:
                    shutil.copyfileobj(src, out, 1 << 20)
                n_files += 1
                n_bytes += m.size
                if n_files % 1000 == 0:
                    log(f"  extracted {n_files} files ({human_bytes(n_bytes)})")
            else:
                raise AcquireError(f"refusing non-regular archive member {m.name!r} (type {m.type!r})")
    return {"files": n_files, "bytes": n_bytes, "top_level": sorted(tops)}


def dataset_root_in(extract_dir: Path, categories: list[str]) -> Path:
    """The archive may hold categories at top level or under one folder."""
    if all((extract_dir / c).is_dir() for c in categories[:1]):
        return extract_dir
    subs = [d for d in extract_dir.iterdir() if d.is_dir()]
    if len(subs) == 1 and (subs[0] / categories[0]).is_dir():
        return subs[0]
    return extract_dir


def validate_extracted(root: Path, plan: Plan, log: Log) -> dict:
    records, report = mvtec.scan(root, plan.categories)
    if plan.expected_counts:
        mvtec.check_expected_counts(report, plan.expected_counts)
    report.errors.extend(mvtec.check_image_mask_sizes(root, records))
    for w in report.warnings[:20]:
        log(f"  warning: {w}")
    if not report.ok:
        shown = "\n  ".join(report.errors[:30])
        raise AcquireError(f"dataset structure check failed ({len(report.errors)} errors):\n  {shown}")
    licence = {}
    for name in ("license.txt", "LICENSE.txt", "readme.txt"):
        p = root / name
        if p.is_file():
            licence[name] = {"sha256": sha256_file(p), "head": p.read_text("utf-8", "replace")[:400]}
    return {"n_records": len(records), "counts": report.counts, "split_hash": mvtec.split_hash(records),
            "n_warnings": len(report.warnings), "archive_text_files": licence}


# ----------------------------------------------------------------------------- orchestration

def _space_check(path: Path, need: int, what: str, log: Log) -> None:
    free = free_bytes(path)
    log(f"free space at {what} ({path}): {human_bytes(free)}; need ~{human_bytes(need)}")
    if free < need:
        raise AcquireError(f"{NO_RETRY_MARK}not enough free space at {what}: {human_bytes(free)} < "
                           f"{human_bytes(need)}")


def _verify_archive_file(path: Path, plan: Plan, log: Log) -> dict:
    check_magic(path)
    size = path.stat().st_size
    if plan.expected_bytes is not None and size != plan.expected_bytes:
        raise AcquireError(f"{path.name}: size {size} != expected {plan.expected_bytes} (recorded from the "
                           "server's Content-Length). Incomplete/corrupt upload, or the publisher changed "
                           "the archive; investigate before overriding expected_bytes in the config.")
    log(f"hashing {path.name} ({human_bytes(size)}) ...")
    digest = sha256_file(path)
    publisher = None
    if plan.publisher_sha256:
        publisher = {"type": "sha256", "value": plan.publisher_sha256, "match": digest == plan.publisher_sha256}
        if not publisher["match"]:
            raise AcquireError(f"publisher SHA-256 mismatch: ours {digest} != publisher {plan.publisher_sha256}")
    elif plan.publisher_md5:
        import hashlib
        h = hashlib.md5()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 23), b""):
                h.update(b)
        publisher = {"type": "md5", "value": plan.publisher_md5, "match": h.hexdigest() == plan.publisher_md5}
        if not publisher["match"]:
            raise AcquireError("publisher MD5 mismatch")
    return {"bytes": size, "sha256_calculated_by_us": digest, "publisher_checksum": publisher}


def _extract_and_validate(archive: Path, plan: Plan, archive_sha: str, log: Log) -> dict:
    tmp = plan.extract_dir.with_name(plan.extract_dir.name + f".tmp-{os.getpid()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        log(f"extracting (safe, single pass) to {tmp} ...")
        stats = safe_extract(archive, tmp, log)
        root = dataset_root_in(tmp, plan.categories)
        info = validate_extracted(root, plan, log)
        if plan.extract_dir.exists():
            shutil.rmtree(plan.extract_dir)
        tmp.rename(plan.extract_dir)
        rel_root = root.relative_to(tmp)
        marker = {"archive_sha256": archive_sha, "extracted_utc": utcnow(),
                  "dataset_root": str(plan.extract_dir / rel_root), "members": stats, **info}
        atomic_write_json(plan.extract_marker, marker)
        return marker
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def _local_extraction_ok(plan: Plan, archive_sha: str) -> dict | None:
    if not plan.extract_marker.exists() or not plan.extract_dir.is_dir():
        return None
    m = read_json(plan.extract_marker)
    if m.get("archive_sha256") != archive_sha:
        return None
    records, report = mvtec.scan(Path(m["dataset_root"]), plan.categories)
    if not report.ok or mvtec.split_hash(records) != m.get("split_hash"):
        return None
    return m


def acquire(plan: Plan, log: Log) -> dict:
    plan.drive_archive_dir.mkdir(parents=True, exist_ok=True)
    plan.local_archive.parent.mkdir(parents=True, exist_ok=True)
    result: dict = {"drive_archive": str(plan.drive_archive)}

    # --- 1. Drive state
    marker = read_json(plan.drive_marker) if plan.drive_marker.exists() else None
    if marker and plan.drive_archive.is_file() and plan.drive_archive.stat().st_size == marker["bytes"]:
        log(f"verified archive already on Drive (sha256 {marker['sha256_calculated_by_us'][:16]}...); "
            "skipping download")
        result["archive_status"] = "already_verified_on_drive"
        sha = marker["sha256_calculated_by_us"]
        existing = _local_extraction_ok(plan, sha)
        if existing:
            log(f"local extraction already verified at {existing['dataset_root']}; nothing to do")
            result.update(extraction_status="already_verified_local", dataset_root=existing["dataset_root"],
                          drive_marker=marker, extraction=existing)
            return result
        _space_check(plan.local_root, marker["bytes"] + plan.extracted_bytes_estimate + plan.margin_bytes,
                     "local disk", log)
        if not (plan.local_archive.is_file() and sha256_file(plan.local_archive) == sha):
            log("staging archive from Drive to local disk ...")
            atomic_copy(plan.drive_archive, plan.local_archive, verify_sha=sha)
        ext = _extract_and_validate(plan.local_archive, plan, sha, log)
        result.update(extraction_status="extracted", dataset_root=ext["dataset_root"], drive_marker=marker,
                      extraction=ext)
        return result
    if marker:
        log("WARNING: Drive marker exists but the archive is missing or a different size; re-verifying")

    if plan.drive_archive.is_file():
        source = {"kind": "manual_upload_or_unverified_drive_copy", "url": None}
        log(f"found unverified archive on Drive ({human_bytes(plan.drive_archive.stat().st_size)}); "
            "verifying it as a manual upload")
        check_magic(plan.drive_archive)
        _space_check(plan.local_root, plan.drive_archive.stat().st_size + plan.extracted_bytes_estimate
                     + plan.margin_bytes, "local disk", log)
        atomic_copy(plan.drive_archive, plan.local_archive)
        headers = None
    else:
        # --- 2. download to local disk
        url, url_source = resolve_url(plan, log)
        headers = probe(url, plan.timeout_s)
        log(f"resolved {url} ({url_source}); server reports {headers['content_type']}, "
            f"{human_bytes(headers['bytes']) if headers['bytes'] else 'unknown size'}")
        if plan.expected_bytes and headers["bytes"] and headers["bytes"] != plan.expected_bytes:
            raise AcquireError(f"{NO_RETRY_MARK}server size {headers['bytes']} != recorded {plan.expected_bytes}; "
                               "the publisher may have changed the archive. Re-verify the official page, "
                               "then update expected_bytes in a NEW config.")
        size = headers["bytes"] or plan.expected_bytes or 6 << 30
        _space_check(plan.local_root, size + plan.extracted_bytes_estimate + plan.margin_bytes, "local disk", log)
        _space_check(plan.drive_archive_dir, size + (256 << 20), "Drive", log)
        part = plan.local_archive.with_name(plan.local_archive.name + ".part")
        if plan.local_archive.is_file():
            log("local archive present from an earlier attempt; verifying instead of re-downloading")
        else:
            t0 = time.time()
            got = stream_download(url, part, headers["bytes"] or plan.expected_bytes, max_retries=plan.max_retries,
                                  timeout=plan.timeout_s, backoff_s=plan.backoff_s, log=log)
            log(f"downloaded {human_bytes(got)} in {time.time() - t0:.0f}s")
            os.replace(part, plan.local_archive)
        source = {"kind": "download", "url": url, "url_source": url_source, "downloaded_utc": utcnow(),
                  "http": headers}

    # --- 3. verify locally (hash + full safe extraction + structure)
    ver = _verify_archive_file(plan.local_archive, plan, log)
    sha = ver["sha256_calculated_by_us"]
    ext = _extract_and_validate(plan.local_archive, plan, sha, log)

    # --- 4. persist on Drive atomically, re-hash the Drive copy, then mark
    if plan.drive_archive.is_file() and sha256_file(plan.drive_archive) == sha:
        log("Drive copy already identical; not re-copying")
    else:
        log(f"copying verified archive to Drive: {plan.drive_archive} ...")
        atomic_copy(plan.local_archive, plan.drive_archive, verify_sha=sha)
    drive_sha = sha256_file(plan.drive_archive)
    if drive_sha != sha:
        raise AcquireError("Drive copy hash mismatch after copy; Drive may be unhealthy. Do not mark verified.")
    marker = {"dataset": "mvtec_ad", "archive_name": plan.archive_name, "source": source, **ver,
              "drive_copy_sha256_reverified": drive_sha, "verified_utc": utcnow(),
              "extraction_check": {k: ext[k] for k in ("members", "n_records", "counts", "split_hash")},
              "note": "sha256_calculated_by_us is OUR hash; publisher_checksum is null when the "
                      "publisher provides none."}
    atomic_write_json(plan.drive_marker, marker)
    log(f"Drive marker written: {plan.drive_marker}")
    result.update(archive_status="verified_and_persisted", drive_marker=marker,
                  extraction_status="extracted", dataset_root=ext["dataset_root"], extraction=ext)
    return result


MANUAL_INSTRUCTIONS = """\
AUTOMATIC ACQUISITION DID NOT COMPLETE. Manual fallback (download/upload only;
no annotation):
 1. Open the official page: {page}
    Click the download entry for the WHOLE dataset (approx. 4.9 GB, file
    "{name}"). If the page shows a form first, complete it yourself.
 2. Expected archive name: {name}  (expected size: {size} bytes)
 3. Upload it, still COMPRESSED (do not extract), to Google Drive at:
    {dest}
 4. Re-run notebook Cell 2 ("Download dataset into Google Drive"). The tool
    detects the uploaded archive, verifies it (XZ magic, size, SHA-256, safe
    extraction, all 15 categories, image-mask pairing) and writes the marker.
"""


def manual_instructions(plan: Plan) -> str:
    return MANUAL_INSTRUCTIONS.format(page=plan.downloads_page, name=plan.archive_name,
                                      size=plan.expected_bytes or "unknown", dest=plan.drive_archive)
