from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from keep_up_with.integrations.base import ToolContext, tool


@dataclass(frozen=True)
class ImageSize:
    width: int
    height: int


@dataclass(frozen=True)
class CropBox:
    x: int
    y: int
    w: int
    h: int
    normalized: bool


@tool("Crop an image with normalized or pixel coordinates")
def crop(
    _ctx: ToolContext,
    input_path: Path = typer.Option(
        ...,
        "--in",
        "-i",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Input image",
    ),
    output_path: Path = typer.Option(..., "--out", "-o", help="Output image"),
    box_value: str = typer.Option(
        ...,
        "--box",
        help="Crop box as x,y,w,h; decimals from 0-1 are normalized",
    ),
) -> dict[str, object]:
    image = _open_image(input_path)
    size = ImageSize(*image.size)
    box = _parse_box(box_value, size)
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cropped = image.crop((box.x, box.y, box.x + box.w, box.y + box.h))
    _save_image(cropped, output_path)

    return {
        "input": str(input_path),
        "output": str(output_path),
        "image": {"width": size.width, "height": size.height},
        "crop": _crop_payload(box, size),
    }


@tool("Draw normalized crop guide lines over an image")
def grid(
    _ctx: ToolContext,
    input_path: Path = typer.Option(
        ...,
        "--in",
        "-i",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Input image",
    ),
    output_path: Path = typer.Option(..., "--out", "-o", help="Output image"),
    major: float = typer.Option(
        0.10,
        "--major",
        help="Major line interval as a normalized fraction",
        min=0.01,
        max=1.0,
    ),
    minor: float = typer.Option(
        0.05,
        "--minor",
        help="Minor line interval as a normalized fraction; use 0 to disable",
        min=0.0,
        max=1.0,
    ),
    labels: bool = typer.Option(
        True,
        "--labels/--no-labels",
        help="Label major grid lines",
    ),
) -> dict[str, object]:
    if minor and minor >= major:
        raise ValueError(f"--minor must be smaller than --major: minor={minor}, major={major}")

    source = _open_image(input_path).convert("RGBA")
    size = ImageSize(*source.size)
    output = _draw_grid(source, size, major=major, minor=minor, labels=labels)
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _save_image(output, output_path)

    return {
        "input": str(input_path),
        "output": str(output_path),
        "image": {"width": size.width, "height": size.height},
        "grid": {
            "major": major,
            "minor": minor,
            "labels": labels,
            "coordinates": "normalized",
        },
    }


def _open_image(path: Path) -> Image.Image:
    try:
        return ImageOps.exif_transpose(Image.open(path))
    except UnidentifiedImageError as error:
        raise ValueError(f"unsupported image file: {path}") from error
    except OSError as error:
        raise ValueError(f"could not open image: {path}: {error}") from error


def _parse_box(value: str, size: ImageSize) -> CropBox:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("--box must be x,y,w,h")

    try:
        numbers = [float(part) for part in parts]
    except ValueError as error:
        raise ValueError("--box must contain numbers") from error

    normalized = all(0 <= number <= 1 for number in numbers)
    if normalized:
        x, y, w, h = (
            round(numbers[0] * size.width),
            round(numbers[1] * size.height),
            round(numbers[2] * size.width),
            round(numbers[3] * size.height),
        )
    else:
        x, y, w, h = (round(number) for number in numbers)

    box = CropBox(x=x, y=y, w=w, h=h, normalized=normalized)
    _validate_box(box, size)
    return box


def _validate_box(box: CropBox, size: ImageSize) -> None:
    if box.w <= 0 or box.h <= 0:
        raise ValueError("crop width and height must be positive")
    if box.x < 0 or box.y < 0:
        raise ValueError("crop offset must be non-negative")
    if box.x + box.w > size.width or box.y + box.h > size.height:
        raise ValueError(
            "crop box exceeds image bounds: "
            f"image={size.width}x{size.height}, crop={box.x},{box.y},{box.w},{box.h}"
        )


def _crop_payload(box: CropBox, size: ImageSize) -> dict[str, object]:
    return {
        "x": box.x,
        "y": box.y,
        "w": box.w,
        "h": box.h,
        "normalized": box.normalized,
        "normalized_box": [
            round(box.x / size.width, 4),
            round(box.y / size.height, 4),
            round(box.w / size.width, 4),
            round(box.h / size.height, 4),
        ],
    }


def _draw_grid(
    image: Image.Image,
    size: ImageSize,
    *,
    major: float,
    minor: float,
    labels: bool,
) -> Image.Image:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    minor_width = 1
    major_width = max(1, min(size.width, size.height) // 1000)

    if minor:
        for fraction in _grid_fractions(minor):
            if _is_major_fraction(fraction, major):
                continue
            _draw_line(draw, [(fraction, 0), (fraction, 1)], size, minor_width, (45, 45, 45, 26))
            _draw_line(draw, [(0, fraction), (1, fraction)], size, minor_width, (45, 45, 45, 26))

    for fraction in _grid_fractions(major):
        _draw_line(draw, [(fraction, 0), (fraction, 1)], size, major_width, (0, 130, 180, 62))
        _draw_line(draw, [(0, fraction), (1, fraction)], size, major_width, (0, 130, 180, 62))

    if labels:
        font = _load_font(size)
        for fraction in _grid_fractions(major):
            label = f"{round(fraction * 100):g}%"
            x = round(fraction * (size.width - 1))
            y = round(fraction * (size.height - 1))
            _draw_label(draw, (x + 4, 4), label, font, size)
            _draw_label(draw, (4, y + 4), label, font, size)

    return Image.alpha_composite(image, overlay)


def _grid_fractions(step: float) -> list[float]:
    values: list[float] = []
    count = round(1 / step)
    for index in range(count + 1):
        value = min(1.0, round(index * step, 6))
        if not values or value != values[-1]:
            values.append(value)
    if values[-1] != 1.0:
        values.append(1.0)
    return values


def _is_major_fraction(fraction: float, major: float) -> bool:
    return abs(round(fraction / major) * major - fraction) < 1e-6


def _draw_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    size: ImageSize,
    width: int,
    color: tuple[int, int, int, int],
) -> None:
    [(x1, y1), (x2, y2)] = points
    coords = (
        round(x1 * (size.width - 1)),
        round(y1 * (size.height - 1)),
        round(x2 * (size.width - 1)),
        round(y2 * (size.height - 1)),
    )
    draw.line(coords, fill=color, width=width)


def _draw_label(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    size: ImageSize,
) -> None:
    x, y = position
    bbox = draw.textbbox((0, 0), text, font=font)
    label_w = bbox[2] - bbox[0] + 8
    label_h = bbox[3] - bbox[1] + 6
    x = min(max(0, x), max(0, size.width - label_w))
    y = min(max(0, y), max(0, size.height - label_h))
    draw.rounded_rectangle(
        (x, y, x + label_w, y + label_h),
        radius=4,
        fill=(255, 255, 255, 145),
        outline=(50, 50, 50, 42),
        width=1,
    )
    draw.text((x + 4, y + 3), text, fill=(35, 35, 35, 135), font=font)


def _load_font(size: ImageSize) -> ImageFont.ImageFont:
    font_size = max(10, min(size.width, size.height) // 85)
    candidates = [
        "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def _save_image(image: Image.Image, output_path: Path) -> None:
    suffix = output_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"} and image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    try:
        image.save(output_path)
    except OSError as error:
        raise ValueError(f"could not save image: {output_path}: {error}") from error
