from __future__ import annotations

import gzip
import re
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
FIGURE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg")


def download_pdf(id_or_url: str, *, output_dir: Path) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_id(arxiv_id)}.pdf"
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
) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    pdf_result = ensure_pdf(arxiv_id, output_dir=output_dir)
    pdf_path = Path(pdf_result["path"])
    target = output or output_dir / f"{safe_id(arxiv_id)}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = convert_pdf_to_markdown(pdf_path)
    target.write_text(text, encoding="utf-8")
    return {
        "id": arxiv_id,
        "pdf_path": str(pdf_path),
        "markdown_path": str(target),
        "characters": len(text),
    }


def download_source(
    id_or_url: str,
    *,
    output_dir: Path,
    extract: bool = True,
) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{safe_id(arxiv_id)}-source.src"
    source_dir = output_dir / f"{safe_id(arxiv_id)}-source"
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

    source_dir.mkdir(parents=True, exist_ok=True)
    if source_type == "tar":
        extract_tar(archive, source_dir)
    else:
        file_name = "main.tex" if source_type.endswith("tex") else "source.bin"
        (source_dir / file_name).write_bytes(single_source_bytes(archive))

    files = [
        path.relative_to(source_dir).as_posix()
        for path in sorted(source_dir.rglob("*"))
        if path.is_file()
    ]
    result["source_dir"] = str(source_dir)
    result["files"] = files
    return result


def collect_figures(id_or_url: str, *, output_dir: Path) -> dict[str, Any]:
    source_result = download_source(id_or_url, output_dir=output_dir, extract=True)
    return figure_inventory(source_result)


def figure_inventory(source_result: dict[str, Any]) -> dict[str, Any]:
    source_dir = Path(str(source_result["source_dir"]))
    if not source_dir.exists():
        raise ValueError("source extraction did not create a source directory")
    references = includegraphics(source_dir)
    figure_files = [
        path.relative_to(source_dir).as_posix()
        for path in sorted(source_dir.rglob("*"))
        if path.is_file() and path.suffix.casefold() in FIGURE_EXTENSIONS
    ]
    return {
        **source_result,
        "includegraphics": references,
        "figure_files": figure_files,
    }


def download(
    id_or_url: str,
    *,
    output_dir: Path,
) -> dict[str, Any]:
    arxiv_id = normalize_id(id_or_url)
    result: dict[str, Any] = {
        "id": arxiv_id,
    }
    result["pdf"] = artifact_result(
        lambda: download_pdf(arxiv_id, output_dir=output_dir)
    )
    result["markdown"] = artifact_result(
        lambda: convert_to_markdown(
            arxiv_id,
            output=None,
            output_dir=output_dir,
        )
    )
    result["source"] = artifact_result(
        lambda: collect_figures(arxiv_id, output_dir=output_dir)
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
        return {"ok": True, "data": action()}
    except Exception as error:
        return {
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }


def ensure_pdf(arxiv_id: str, *, output_dir: Path) -> dict[str, Any]:
    path = output_dir / f"{safe_id(arxiv_id)}.pdf"
    if path.exists():
        return {
            "id": arxiv_id,
            "path": str(path),
            "url": ARXIV_PDF.format(id=arxiv_id),
        }
    return download_pdf(arxiv_id, output_dir=output_dir)


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


def convert_pdf_to_markdown(pdf_path: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as error:
        raise ValueError("markitdown is required for arXiv Markdown conversion") from error

    result = MarkItDown().convert(str(pdf_path))
    content = getattr(result, "text_content", None)
    if not isinstance(content, str):
        content = getattr(result, "markdown", None)
    if not isinstance(content, str):
        content = str(result)
    return content


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
