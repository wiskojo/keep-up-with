from __future__ import annotations

import gzip
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

ARXIV_PDF = "https://arxiv.org/pdf/{id}"
ARXIV_SOURCE = "https://arxiv.org/src/{id}"
ID_RE = re.compile(
    r"(?:arxiv:)?(?P<id>(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)",
    re.IGNORECASE,
)
GRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\[[^\]]*\])?\{(?P<path>[^}]+)\}",
)
HTML_SRC_RE = re.compile(
    r"(?P<prefix>\bsrc=[\"'])(?P<path>[^\"']+)(?P<suffix>[\"'])",
)
MARKDOWN_IMAGE_RE = re.compile(
    r"(?P<prefix>!\[[^\]]*\]\()(?P<path>[^)\s]+)(?P<suffix>\))",
)
FIGURE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg")


def download_pdf(id_or_url: str, *, output_dir: Path) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "paper.pdf"
    download_file(ARXIV_PDF.format(id=arxiv_id), path)
    return {
        "id": arxiv_id,
        "path": str(path),
        "url": ARXIV_PDF.format(id=arxiv_id),
    }


def convert_to_markdown(
    id_or_url: str,
    *,
    output: Path | None,
    output_dir: Path,
    source_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    target = output or output_dir / "paper.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "paper.pdf"
    if not source_result or not source_result.get("ok") or not source_result.get("source_dir"):
        raise ValueError("arXiv source is required for Markdown conversion")
    text = convert_source_to_markdown(Path(str(source_result["source_dir"])))
    if not text.strip():
        raise ValueError("pandoc produced empty Markdown output")
    target.write_text(text, encoding="utf-8")
    return {
        "id": arxiv_id,
        "pdf_path": str(pdf_path),
        "markdown_path": str(target),
        "characters": len(text),
        "method": "pandoc",
    }


def download_source(
    id_or_url: str,
    *,
    output_dir: Path,
    extract: bool = True,
) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    archive = source_dir / "source.src"
    download_file(ARXIV_SOURCE.format(id=arxiv_id), archive)

    source_type = detect_source_type(archive)
    result: dict[str, Any] = {
        "id": arxiv_id,
        "source_path": str(archive),
        "source_url": ARXIV_SOURCE.format(id=arxiv_id),
        "source_dir": "",
        "source_type": source_type,
        "files": [],
    }
    if not extract:
        return result

    if source_type == "tar":
        extract_tar(archive, source_dir)
    else:
        file_name = "main.tex" if source_type.endswith("tex") else "source.bin"
        (source_dir / file_name).write_bytes(single_source_bytes(archive))

    files = [
        path.relative_to(source_dir).as_posix()
        for path in sorted(source_dir.rglob("*"))
        if path.is_file() and path != archive
    ]
    result["source_dir"] = str(source_dir)
    result["files"] = files
    return result


def collect_figures(source_result: dict[str, Any], *, media_dir: Path) -> dict[str, Any]:
    return figure_inventory(source_result, media_dir=media_dir)


def figure_inventory(source_result: dict[str, Any], *, media_dir: Path) -> dict[str, Any]:
    source_dir = Path(str(source_result["source_dir"]))
    if not source_dir.exists():
        raise ValueError("source extraction did not create a source directory")
    references = includegraphics(source_dir)
    figure_files = [
        path.relative_to(source_dir).as_posix()
        for path in sorted(source_dir.rglob("*"))
        if path.is_file() and path.suffix.casefold() in FIGURE_EXTENSIONS
    ]
    media_files = copy_figures(source_dir, figure_files, media_dir=media_dir)
    return {
        **source_result,
        "includegraphics": references,
        "figure_files": figure_files,
        "media_dir": str(media_dir),
        "media_files": media_files,
    }


def download(
    id_or_url: str,
    *,
    output_dir: Path,
) -> dict[str, Any]:
    require_pandoc()
    arxiv_id = normalize_id(id_or_url)
    target_dir = output_dir / f"arxiv-paper-{safe_id(arxiv_id)}"
    media_dir = target_dir / "media"
    result: dict[str, Any] = {
        "id": arxiv_id,
        "type": "arxiv_paper",
        "directory": str(target_dir),
    }
    result["pdf"] = artifact_result(
        lambda: pdf_artifact(download_pdf(arxiv_id, output_dir=target_dir))
    )
    source_result = artifact_result(
        lambda: download_source(arxiv_id, output_dir=target_dir, extract=True)
    )
    media_result = artifact_result(
        lambda: collect_figures(source_result, media_dir=media_dir)
    )
    result["source"] = source_artifact(source_result)
    result["media"] = media_artifact(media_result, media_dir=media_dir)
    result["markdown"] = markdown_artifact(
        convert_to_markdown(
            arxiv_id,
            output=None,
            output_dir=target_dir,
            source_result=source_result,
        )
    )
    result["json"] = artifact_result(
        lambda: write_json_artifact(
            target_dir / "paper.json",
            {key: value for key, value in result.items() if key != "json"},
        )
    )
    return result


def normalize_id(value: str) -> str:
    text_value = value.strip()
    parsed = urlparse(text_value)
    if parsed.netloc.endswith("arxiv.org"):
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"abs", "pdf", "e-print", "src"}:
            arxiv_id = parts[1]
            new_style_id = re.fullmatch(
                r"\d{4}\.\d{4,5}(?:v\d+)?(?:\.pdf)?",
                arxiv_id,
            )
            if "/" in text_value and not new_style_id and len(parts) >= 3:
                arxiv_id = f"{parts[1]}/{parts[2]}"
            if parts[0] == "pdf" and arxiv_id.endswith(".pdf"):
                arxiv_id = arxiv_id[:-4]
            return arxiv_id
    match = ID_RE.search(text_value)
    if not match:
        raise ValueError(f"could not find arXiv id in: {value}")
    return match.group("id")


def safe_id(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_")


def artifact_result(action) -> dict[str, Any]:
    try:
        return {"ok": True, **action()}
    except Exception as error:
        return {
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }


def pdf_artifact(result: dict[str, Any]) -> dict[str, Any]:
    return {"path": result["path"], "url": result["url"]}


def markdown_artifact(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "path": result["markdown_path"],
        "characters": result["characters"],
        "pdf_path": result["pdf_path"],
        "method": result["method"],
    }


def source_artifact(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return result
    artifact = {
        "ok": True,
        "directory": result["source_dir"],
        "archive_path": result["source_path"],
        "source_url": result["source_url"],
        "source_type": result["source_type"],
        "files": result["files"],
    }
    if "figure_files" in result:
        artifact["figure_files"] = result["figure_files"]
    if "includegraphics" in result:
        artifact["includegraphics"] = result["includegraphics"]
    return artifact


def media_artifact(result: dict[str, Any], *, media_dir: Path) -> dict[str, Any]:
    if not result.get("ok"):
        return {
            "ok": False,
            "directory": str(media_dir),
            "files": [],
            "errors": [{"error": result.get("error", "source download failed")}],
        }
    return {
        "ok": True,
        "directory": result["media_dir"],
        "files": result["media_files"],
        "errors": [],
    }


def write_json_artifact(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path)}


def copy_figures(source_dir: Path, figure_files: list[str], *, media_dir: Path) -> list[str]:
    media_files: list[str] = []
    for item in figure_files:
        source = source_dir / item
        if not source.is_file():
            continue
        if source.suffix.casefold() == ".pdf":
            target = (media_dir / item).with_suffix(".png")
            convert_pdf_figure(source, target)
        else:
            target = media_dir / item
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        media_files.append(str(target))
    return media_files


def convert_pdf_figure(source: Path, target: Path) -> None:
    if shutil.which("pdftoppm") is None:
        raise ValueError("pdftoppm is required to convert PDF figures")
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = target.with_suffix("")
    try:
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-singlefile",
                "-r",
                "200",
                str(source),
                str(prefix),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip() or "unknown pdftoppm error"
        raise ValueError(f"failed to convert PDF figure {source}: {detail}") from error


def download_file(url: str, path: Path) -> None:
    with httpx.stream("GET", url, timeout=60, follow_redirects=True) as response:
        response.raise_for_status()
        with path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)


def detect_source_type(archive: Path) -> str:
    if tarfile.is_tarfile(archive):
        return "tar"
    try:
        data = gzip.decompress(archive.read_bytes())
    except OSError:
        data = archive.read_bytes()
        compressed = False
    else:
        compressed = True
    if looks_like_tex(data):
        return "single-file-gzip-tex" if compressed else "single-file-tex"
    return "single-file-gzip-binary" if compressed else "single-file-binary"


def single_source_bytes(archive: Path) -> bytes:
    try:
        return gzip.decompress(archive.read_bytes())
    except OSError:
        return archive.read_bytes()


def looks_like_tex(data: bytes) -> bool:
    sample = data[:8192].decode("utf-8", errors="ignore")
    return any(
        marker in sample
        for marker in (
            "\\documentclass",
            "\\begin{document}",
            "\\section",
            "\\includegraphics",
        )
    )


def convert_source_to_markdown(source_dir: Path) -> str:
    main = main_tex_file(source_dir)
    if main is None:
        raise ValueError("arXiv source does not contain a TeX file")
    require_pandoc()
    try:
        result = subprocess.run(
            [
                "pandoc",
                "--from",
                "latex",
                "--to",
                "gfm",
                "--wrap=none",
                main.name,
            ],
            cwd=main.parent,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("pandoc timed out while converting arXiv source") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip() or "unknown pandoc error"
        raise ValueError(f"pandoc failed while converting arXiv source: {detail}") from error
    except OSError as error:
        raise ValueError(f"pandoc failed while converting arXiv source: {error}") from error
    text = rewrite_markdown_asset_paths(
        result.stdout.strip(),
        base_dir=main.parent,
        source_dir=source_dir,
    )
    return f"{text}\n" if text else ""


def require_pandoc() -> None:
    if shutil.which("pandoc") is None:
        raise ValueError("pandoc is required for arXiv Markdown conversion")


def rewrite_markdown_asset_paths(text: str, *, base_dir: Path, source_dir: Path) -> str:
    def html_replace(match: re.Match[str]) -> str:
        path = source_relative_path(
            match.group("path"),
            base_dir=base_dir,
            source_dir=source_dir,
        )
        return f"{match.group('prefix')}{path}{match.group('suffix')}"

    def markdown_replace(match: re.Match[str]) -> str:
        path = source_relative_path(
            match.group("path"),
            base_dir=base_dir,
            source_dir=source_dir,
        )
        return f"{match.group('prefix')}{path}{match.group('suffix')}"

    text = HTML_SRC_RE.sub(html_replace, text)
    return MARKDOWN_IMAGE_RE.sub(markdown_replace, text)


def source_relative_path(value: str, *, base_dir: Path, source_dir: Path) -> str:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith(("/", "#")):
        return value
    resolved = (base_dir / parsed.path).resolve()
    try:
        relative = resolved.relative_to(source_dir.resolve())
    except ValueError:
        return value
    path = f"source/{relative.as_posix()}"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"
    return path


def main_tex_file(source_dir: Path) -> Path | None:
    candidates = sorted(source_dir.rglob("*.tex"))
    document_files = [
        path
        for path in candidates
        if "\\begin{document}" in path.read_text(encoding="utf-8", errors="replace")
    ]
    if not document_files:
        return candidates[0] if candidates else None
    for name in ("main.tex", "ms.tex", "paper.tex"):
        for path in document_files:
            if path.name == name:
                return path
    return document_files[0]


def extract_tar(archive: Path, output_dir: Path) -> None:
    with tarfile.open(archive) as tar:
        root = output_dir.resolve()
        for member in tar.getmembers():
            target = (output_dir / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                raise ValueError(f"unsafe path in arXiv source archive: {member.name}")
        tar.extractall(output_dir)


def includegraphics(source_dir: Path) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for tex in sorted(source_dir.rglob("*.tex")):
        try:
            lines = tex.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for match in GRAPHICS_RE.finditer(line):
                raw_path = match.group("path")
                resolved = resolve_figure_path(source_dir, tex.parent, raw_path)
                references.append(
                    {
                        "tex_file": tex.relative_to(source_dir).as_posix(),
                        "line": line_number,
                        "path": raw_path,
                        "resolved": (
                            resolved.relative_to(source_dir).as_posix()
                            if resolved is not None
                            else ""
                        ),
                    }
                )
    return references


def resolve_figure_path(source_dir: Path, base: Path, raw_path: str) -> Path | None:
    for root in (base, source_dir):
        candidate = root / raw_path
        if candidate.exists():
            return candidate
        if candidate.suffix:
            continue
        for suffix in FIGURE_EXTENSIONS:
            with_suffix = candidate.with_suffix(suffix)
            if with_suffix.exists():
                return with_suffix
    return None
