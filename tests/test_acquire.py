"""Acquisition: resolve link, reject HTML, resume, verify, persist, skip, manual upload, unsafe paths."""
import http.server
import threading
from pathlib import Path

import pytest

from anomaly_memory.data import acquire as A
from anomaly_memory.io_utils import read_json, sha256_file
from conftest import make_archive, make_fake_mvtec

CATS = ["bottle", "carpet"]


class Server:
    def __init__(self, archive: Path, name: str):
        self.archive, self.name = archive, name
        self.mode = "ok"  # ok | html | flaky
        self.requests = []
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_HEAD(self):
                self._serve(head=True)

            def do_GET(self):
                self._serve(head=False)

            def _serve(self, head):
                outer.requests.append((self.command, self.path, self.headers.get("Range")))
                if self.path == "/downloads":
                    body = f'<a href="/files/{outer.name}">whole</a><a href="/files/x.tar.xz">x</a>'.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    if not head:
                        self.wfile.write(body)
                    return
                if outer.mode == "html":
                    body = b"<html>please log in</html>"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    if not head:
                        self.wfile.write(body)
                    return
                data = outer.archive.read_bytes()
                start = 0
                rng = self.headers.get("Range")
                if rng:
                    start = int(rng.split("=")[1].split("-")[0])
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
                else:
                    self.send_response(200)
                chunk = data[start:]
                if outer.mode == "flaky" and not head and start == 0:
                    chunk = chunk[: len(chunk) // 2]  # truncated transfer -> must resume
                self.send_header("Content-Type", "application/x-xz")
                self.send_header("Content-Length", str(len(chunk)))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                if not head:
                    self.wfile.write(chunk)

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def close(self):
        self.httpd.shutdown()


@pytest.fixture
def setup(tmp_path):
    src = make_fake_mvtec(tmp_path / "src", categories=CATS)
    archive = make_archive(src, tmp_path / "mvtec.tar.xz")
    srv = Server(archive, "mvtec.tar.xz")
    plan = A.Plan(archive_name="mvtec.tar.xz", downloads_page=srv.base + "/downloads",
                  fallback_url=srv.base + "/files/mvtec.tar.xz", expected_bytes=archive.stat().st_size,
                  extracted_bytes_estimate=1 << 20, publisher_sha256=None, publisher_md5=None,
                  drive_archive_dir=tmp_path / "drive" / "datasets" / "archives", local_root=tmp_path / "local",
                  extracted_dirname="mvtec_ad", categories=CATS, expected_counts=None, max_retries=3,
                  timeout_s=10, backoff_s=0.01, margin_bytes=0)
    yield plan, srv, archive
    srv.close()


def test_full_flow_then_skip(setup):
    plan, srv, archive = setup
    r = A.acquire(plan, print)
    assert r["archive_status"] == "verified_and_persisted"
    m = read_json(plan.drive_marker)
    assert m["sha256_calculated_by_us"] == sha256_file(archive) == sha256_file(plan.drive_archive)
    assert m["publisher_checksum"] is None and m["source"]["url_source"] == "downloads_page"
    assert Path(r["dataset_root"], "bottle", "train", "good").is_dir()
    n = len(srv.requests)
    r2 = A.acquire(plan, print)
    assert r2["archive_status"] == "already_verified_on_drive"
    assert r2["extraction_status"] == "already_verified_local"
    assert len(srv.requests) == n  # nothing downloaded again


def test_new_runtime_restages_from_drive(setup):
    plan, srv, _ = setup
    A.acquire(plan, print)
    import shutil
    shutil.rmtree(plan.local_root)  # fresh runtime: local disk empty, Drive persists
    n = len(srv.requests)
    r = A.acquire(plan, print)
    assert r["extraction_status"] == "extracted" and len(srv.requests) == n


def test_resume_after_truncated_transfer(setup):
    plan, srv, archive = setup
    srv.mode = "flaky"
    A.acquire(plan, print)
    assert any(rng for _, _, rng in srv.requests if rng)
    assert sha256_file(plan.drive_archive) == sha256_file(archive)


def test_html_disguised_as_archive_rejected(setup):
    plan, srv, _ = setup
    srv.mode = "html"
    with pytest.raises(A.NotAnArchive):
        A.acquire(plan, print)
    assert not plan.drive_marker.exists() and not plan.drive_archive.exists()


def test_manual_upload_detected_and_verified(setup):
    plan, srv, archive = setup
    plan.drive_archive_dir.mkdir(parents=True)
    import shutil
    shutil.copyfile(archive, plan.drive_archive)
    srv.close()  # no network needed
    r = A.acquire(plan, print)
    assert r["archive_status"] == "verified_and_persisted"
    assert read_json(plan.drive_marker)["source"]["kind"].startswith("manual_upload")


def test_corrupt_manual_upload_rejected(setup):
    plan, _, _ = setup
    plan.drive_archive_dir.mkdir(parents=True)
    plan.drive_archive.write_bytes(b"<html>not an archive</html>")
    with pytest.raises(A.NotAnArchive):
        A.acquire(plan, print)
    assert not plan.drive_marker.exists()


def test_publisher_checksum_mismatch(setup):
    plan, _, _ = setup
    plan.publisher_sha256 = "0" * 64
    with pytest.raises(A.AcquireError, match="publisher SHA-256 mismatch"):
        A.acquire(plan, print)
    assert not plan.drive_marker.exists()


def test_unsafe_paths_and_structure(tmp_path):
    src = make_fake_mvtec(tmp_path / "s", categories=CATS)
    evil = make_archive(src, tmp_path / "evil.tar.xz", extra_members=[("../escape.txt", b"x")])
    with pytest.raises(A.AcquireError, match="unsafe"):
        A.safe_extract(evil, tmp_path / "out", print)
    (src / "carpet" / "ground_truth" / "hole" / "000_mask.png").unlink()
    from anomaly_memory.data import mvtec
    _, rep = mvtec.scan(src, CATS)
    assert any("missing mask" in e for e in rep.errors)


def test_resolve_falls_back_with_warning(setup):
    plan, srv, _ = setup
    plan.downloads_page = srv.base + "/nothing-here"
    srv.mode = "html"
    url, src = A.resolve_url(plan, print)
    assert src == "fallback_recorded_url" and url == plan.fallback_url


def test_manual_instructions_mention_everything(setup):
    plan, _, _ = setup
    text = A.manual_instructions(plan)
    for s in (plan.downloads_page, plan.archive_name, str(plan.drive_archive), "COMPRESSED", "Cell 2"):
        assert s in text
