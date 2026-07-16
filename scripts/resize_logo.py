#!/usr/bin/env python3
"""Script to automatically resize the original logo into optimized web assets.

Reads the high-resolution source logo (transparent background), trims empty
padding, and outputs standard size variations for the UI, docs, report PDFs,
and favicons without upscaling.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field


class ResizedLogoSpec(BaseModel):
    """Specification for a resized logo image output configuration.

    Attributes:
        filename (str): Name of the generated output file.
        height (int | None): Target height in pixels for aspect-ratio preservation.
        is_square (bool): True if image should be centered and padded on a square canvas.
        square_size (int | None): Size of the square canvas in pixels.
        remove_background (bool): True if solid black/checkerboard backgrounds should be removed.
        redraw_manager (bool): True to replace the MANAGER subtitle with crisp vector text.
        output_dir (Path): Target directory to save the image.
    """

    model_config = {"extra": "forbid"}

    filename: str = Field(description="Name of the output file.")
    height: int | None = Field(default=None, description="Target height in pixels.")
    is_square: bool = Field(
        default=False, description="True if output should be a square canvas."
    )
    square_size: int | None = Field(
        default=None, description="Size of the square canvas in pixels."
    )
    remove_background: bool = Field(
        default=False,
        description=(
            "True if solid black or checkerboard backgrounds should be removed. "
            "Leave False for sources that already have a transparent background."
        ),
    )
    redraw_manager: bool = Field(
        default=False,
        description=(
            "True to clear the downscaled MANAGER subtitle and redraw it with "
            "crisp text sized for the output canvas."
        ),
    )
    output_dir: Path = Field(description="Output target directory.")


class LogoResizerConfig(BaseModel):
    """Configuration for the logo resizer process.

    Attributes:
        source_path (Path): Path to the high-resolution source logo.
        specs (list[ResizedLogoSpec]): List of image specifications to generate.
    """

    model_config = {"extra": "forbid"}

    source_path: Path = Field(description="Path to the source logo file.")
    specs: list[ResizedLogoSpec] = Field(description="List of target specifications.")


class LogoResizer:
    """A tool for generating optimized, resized images from a source logo.

    Handles residual background removal, aspect-ratio resizing without
    upscaling, and square padded icon generation.
    """

    def __init__(self, config: LogoResizerConfig) -> None:
        """Initialize the resizer with configuration.

        Args:
            config (LogoResizerConfig): The configuration containing source paths and specs.
        """
        self.config = config

    def _remove_checkerboard_background(self, img: Image.Image) -> Image.Image:
        """Remove solid black, checkerboard, and connected background pixels.

        Uses a BFS traversal seeded from image borders and existing transparent
        pixels to find all connected background-like pixels and convert them to
        transparent.

        Args:
            img (Image.Image): The source PIL image object.

        Returns:
            Image.Image: The PIL image object with background removed.
        """
        logger.info("Detecting and removing background...")
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()

        visited = set()

        def is_bg_pixel(x: int, y: int) -> bool:
            r, g, b, a = pixels[x, y]
            if a < 128:
                return True
            # Solid black or near-black background only. Do not treat light grey or
            # near-white as background — those colors appear in metallic logo text.
            if max(r, g, b) < 45:
                return True
            return False

        # Queue for BFS
        queue = deque()

        # Seed from transparent pixels and border background pixels.
        for x in range(width):
            for y in [0, height - 1]:
                if is_bg_pixel(x, y) and (x, y) not in visited:
                    queue.append((x, y))
                    visited.add((x, y))
        for y in range(height):
            for x in [0, width - 1]:
                if (x, y) not in visited and is_bg_pixel(x, y):
                    queue.append((x, y))
                    visited.add((x, y))
        for y in range(height):
            for x in range(width):
                if pixels[x, y][3] < 128 and (x, y) not in visited:
                    queue.append((x, y))
                    visited.add((x, y))

        bg_pixel_count = 0
        # BFS traversal
        while queue:
            cx, cy = queue.popleft()
            pixels[cx, cy] = (0, 0, 0, 0)
            bg_pixel_count += 1

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in visited and is_bg_pixel(nx, ny):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        logger.info(
            f"Background removal complete. Converted {bg_pixel_count} pixels to transparent."
        )
        return img

    def _trim_to_content(
        self, img: Image.Image, *, treat_near_black_as_empty: bool = False
    ) -> Image.Image:
        """Crop transparent or empty padding from around visible logo content.

        Args:
            img (Image.Image): The source PIL image object.
            treat_near_black_as_empty (bool): True to ignore near-black pixels when
                computing the crop bounds.

        Returns:
            Image.Image: The cropped PIL image object.
        """
        img = img.convert("RGBA")
        if not treat_near_black_as_empty:
            bbox = img.getbbox()
            if bbox is None:
                return img
            cropped = img.crop(bbox)
            logger.debug(f"Trimmed transparent padding to bounds: {bbox}")
            return cropped

        width, height = img.size
        pixels = img.load()
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        found_content = False

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 20 or max(r, g, b) < 45:
                    continue
                found_content = True
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        if not found_content:
            return img

        bbox = (min_x, min_y, max_x + 1, max_y + 1)
        logger.debug(f"Trimmed near-black padding to bounds: {bbox}")
        return img.crop(bbox)

    def _resize_aspect_ratio(self, img: Image.Image, target_height: int) -> Image.Image:
        """Resize the image to a maximum height while preserving aspect ratio.

        Returns the source-sized image when the requested height would require
        upscaling, which avoids introducing interpolation blur and artifacts.

        Args:
            img (Image.Image): The source PIL image object.
            target_height (int): The maximum target height in pixels.

        Returns:
            Image.Image: The resized PIL image object.
        """
        w, h = img.size
        if target_height >= h:
            logger.debug(
                f"Keeping source dimensions {w}x{h}; "
                f"requested height {target_height} would upscale the image"
            )
            return img.copy()

        aspect = w / h
        target_width = int(target_height * aspect)
        logger.debug(f"Resizing to aspect ratio: {target_width}x{target_height}")
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    def _create_square_canvas(self, img: Image.Image, size: int) -> Image.Image:
        """Fit the image inside a transparent square canvas of the specified size.

        Args:
            img (Image.Image): The source PIL image object.
            size (int): The target width and height of the canvas.

        Returns:
            Image.Image: The square padded PIL image object.
        """
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        w, h = img.size
        aspect = w / h

        if aspect >= 1.0:
            new_w = size
            new_h = int(size / aspect)
        else:
            new_h = size
            new_w = int(size * aspect)

        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        x_offset = (size - new_w) // 2
        y_offset = (size - new_h) // 2

        canvas.paste(resized, (x_offset, y_offset))
        logger.debug(
            f"Created square canvas: {size}x{size} with image size {new_w}x{new_h}"
        )
        return canvas

    def _load_manager_font(
        self, size: int
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Load a bold sans-serif font for the MANAGER subtitle.

        Args:
            size (int): Requested font size in pixels.

        Returns:
            ImageFont.FreeTypeFont | ImageFont.ImageFont: Loaded font face.
        """
        candidates = [
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/HelveticaNeue.ttc"),
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
        for path in candidates:
            if not path.exists():
                continue
            try:
                if path.suffix.lower() == ".ttc":
                    return ImageFont.truetype(str(path), size=size, index=0)
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
        logger.warning("Falling back to PIL default font for MANAGER subtitle")
        return ImageFont.load_default()

    def _find_oracle_license_bounds(
        self, img: Image.Image
    ) -> tuple[int, int, int] | None:
        """Locate the blue Oracle License wordmark bounds.

        Ignores pale cyan accent lines used beside MANAGER so the wordmark
        bottom edge is not pushed into the subtitle band.

        Args:
            img (Image.Image): Source or resized logo image.

        Returns:
            tuple[int, int, int] | None: (left_x, right_x, bottom_y) when found,
            otherwise None.
        """
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()
        blue_xs: list[int] = []
        blue_ys: list[int] = []
        search_top = max(0, int(height * 0.45))
        search_bottom = int(height * 0.92)
        for y in range(search_top, search_bottom):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 100:
                    continue
                saturation = max(r, g, b) - min(r, g, b)
                # Saturated blue fill/outline of Oracle License, not pale accent rules.
                if b > 140 and b > r + 25 and b >= g and saturation >= 50:
                    blue_xs.append(x)
                    blue_ys.append(y)
        if not blue_ys:
            return None
        return min(blue_xs), max(blue_xs), max(blue_ys)

    def _find_manager_band_top(self, img: Image.Image) -> int | None:
        """Find the top edge of the existing MANAGER subtitle band.

        Args:
            img (Image.Image): Trimmed source logo.

        Returns:
            int | None: Y coordinate of the subtitle band top, or None if absent.
        """
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()
        # Stay below the Oracle License wordmark region.
        search_top = int(height * 0.88)
        for y in range(search_top, height):
            bright = 0
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 120:
                    continue
                if min(r, g, b) > 170 and abs(r - g) < 35 and abs(g - b) < 35:
                    bright += 1
            if bright >= max(8, width // 20):
                return max(0, y - 2)
        return None

    def _render_manager_subtitle(
        self,
        *,
        canvas_width: int,
        slot_height: int,
        ol_left: int,
        ol_right: int,
    ) -> Image.Image:
        """Render a crisp MANAGER subtitle strip for a reserved vertical slot.

        Args:
            canvas_width (int): Full logo width in pixels.
            slot_height (int): Height reserved for the subtitle strip.
            ol_left (int): Left edge of the Oracle License wordmark.
            ol_right (int): Right edge of the Oracle License wordmark.

        Returns:
            Image.Image: Transparent strip containing MANAGER text and rules.
        """
        scale = 4
        text = "MANAGER"
        target_text_h = max(10, int(slot_height * 0.58))
        font = self._load_manager_font(target_text_h * scale)
        spacing = max(scale, target_text_h * scale // 7)

        def spaced_width(font_obj: ImageFont.ImageFont, gap: int) -> int:
            total = 0
            for index, char in enumerate(text):
                bbox = font_obj.getbbox(char)
                total += bbox[2] - bbox[0]
                if index < len(text) - 1:
                    total += gap
            return total

        text_w = spaced_width(font, spacing)
        bbox = font.getbbox(text)
        text_h = bbox[3] - bbox[1]
        pad = 2 * scale
        canvas = Image.new(
            "RGBA",
            (text_w + pad * 2, text_h + pad * 2),
            (0, 0, 0, 0),
        )
        draw = ImageDraw.Draw(canvas)
        cursor_x = pad - bbox[0]
        cursor_y = pad - bbox[1]
        # Soft drop shadows look muddy on tiny canvases; skip them there.
        draw_shadow = slot_height > 28
        if draw_shadow:
            shadow_x = cursor_x
            for char in text:
                draw.text(
                    (shadow_x + scale // 2, cursor_y + scale // 2),
                    char,
                    font=font,
                    fill=(20, 30, 50, 120),
                )
                char_w = font.getbbox(char)[2] - font.getbbox(char)[0]
                shadow_x += char_w + spacing
        for char in text:
            draw.text((cursor_x, cursor_y), char, font=font, fill=(236, 240, 248, 255))
            char_w = font.getbbox(char)[2] - font.getbbox(char)[0]
            cursor_x += char_w + spacing

        subtitle = canvas.resize(
            (max(1, canvas.width // scale), max(1, canvas.height // scale)),
            Image.Resampling.LANCZOS,
        )

        strip = Image.new("RGBA", (canvas_width, slot_height), (0, 0, 0, 0))
        paste_x = (canvas_width - subtitle.width) // 2
        paste_y = max(0, (slot_height - subtitle.height) // 2)
        line_y = paste_y + subtitle.height // 2
        gap = max(4, canvas_width // 40)
        line_color = (195, 215, 240, 255)
        thickness = max(1, slot_height // 10)
        overlay = ImageDraw.Draw(strip)
        left_end = paste_x - gap
        right_start = paste_x + subtitle.width + gap
        if left_end > ol_left + 2:
            overlay.line(
                [(ol_left, line_y), (left_end, line_y)],
                fill=line_color,
                width=thickness,
            )
        if ol_right - 2 > right_start:
            overlay.line(
                [(right_start, line_y), (ol_right, line_y)],
                fill=line_color,
                width=thickness,
            )
        strip.alpha_composite(subtitle, (paste_x, paste_y))
        return strip

    def _compose_with_crisp_manager(
        self, img: Image.Image, target_height: int
    ) -> Image.Image:
        """Resize the mark while reserving vertical space for a crisp MANAGER label.

        Crops away the source subtitle, scales the shield and Oracle License
        wordmark into the remaining height, then draws a vector MANAGER strip.

        Args:
            img (Image.Image): Trimmed source logo.
            target_height (int): Final output height in pixels.

        Returns:
            Image.Image: Composed logo with a crisp MANAGER subtitle.
        """
        bounds = self._find_oracle_license_bounds(img)
        if bounds is None:
            logger.warning(
                "Could not locate Oracle License wordmark; falling back to plain resize"
            )
            return self._resize_aspect_ratio(img, target_height)

        ol_left, ol_right, ol_bottom = bounds
        manager_top = self._find_manager_band_top(img)
        # Keep the full Oracle License wordmark; only crop once we are past it.
        crop_bottom = ol_bottom + 2
        if manager_top is not None and manager_top > ol_bottom:
            crop_bottom = manager_top
        upper = img.crop((0, 0, img.width, min(img.height, crop_bottom)))
        manager_slot = max(14, int(target_height * 0.22))
        upper_height = max(8, target_height - manager_slot)
        upper_resized = self._resize_aspect_ratio(upper, upper_height)

        scale_x = upper_resized.width / upper.width
        scaled_ol_left = int(ol_left * scale_x)
        scaled_ol_right = int(ol_right * scale_x)

        canvas = Image.new(
            "RGBA",
            (upper_resized.width, target_height),
            (0, 0, 0, 0),
        )
        canvas.paste(upper_resized, (0, 0), upper_resized)
        subtitle = self._render_manager_subtitle(
            canvas_width=canvas.width,
            slot_height=manager_slot,
            ol_left=scaled_ol_left,
            ol_right=scaled_ol_right,
        )
        canvas.alpha_composite(subtitle, (0, upper_resized.height))
        logger.debug(
            f"Composed crisp MANAGER logo {canvas.size} "
            f"(upper={upper_resized.size}, slot={manager_slot})"
        )
        return canvas

    def process_spec(self, spec: ResizedLogoSpec) -> None:
        """Process a single image specification.

        Args:
            spec (ResizedLogoSpec): The image specification to generate.

        Raises:
            ValueError: If specifications are invalid (e.g. missing sizes).
        """
        logger.info(f"Generating specification: {spec.filename} in {spec.output_dir}")
        spec.output_dir.mkdir(parents=True, exist_ok=True)
        dest_path = spec.output_dir / spec.filename

        with Image.open(self.config.source_path) as raw_img:
            img = (
                self._remove_checkerboard_background(raw_img)
                if spec.remove_background
                else raw_img.convert("RGBA")
            )
            # Prefer alpha-based trimming so metallic silver/white logo text is preserved.
            img = self._trim_to_content(img, treat_near_black_as_empty=False)

            if spec.is_square:
                if not spec.square_size:
                    raise ValueError(
                        f"square_size must be specified for square spec {spec.filename}"
                    )
                processed_img = self._create_square_canvas(img, spec.square_size)
            else:
                if not spec.height:
                    raise ValueError(
                        f"height must be specified for non-square spec {spec.filename}"
                    )
                if spec.redraw_manager:
                    processed_img = self._compose_with_crisp_manager(img, spec.height)
                else:
                    processed_img = self._resize_aspect_ratio(img, spec.height)

            # Save the image with PNG optimization
            processed_img.save(dest_path, "PNG", optimize=True)
            logger.info(f"Successfully saved optimized image to {dest_path}")

    def run(self) -> None:
        """Execute the resizing process for all specifications in the configuration."""
        logger.info(
            f"Starting logo resizing process for source: {self.config.source_path}"
        )
        for spec in self.config.specs:
            self.process_spec(spec)
        logger.info("Logo resizing process completed successfully.")


def main() -> None:
    """Main entry point to execute the logo resizing script."""
    root_dir = Path(__file__).resolve().parent.parent
    source = root_dir / "assets/olm_logo.png"
    assets_dir = root_dir / "frontend/src/assets"
    public_dir = root_dir / "frontend/public"
    report_assets_dir = root_dir / "backend/src/license_tracker/assets"
    docs_images_dir = root_dir / "docs/images"

    if not source.exists():
        logger.error(f"Source logo not found at: {source}")
        sys.exit(1)

    config = LogoResizerConfig(
        source_path=source,
        specs=[
            # App UI sizes (transparent background works on light and dark themes)
            ResizedLogoSpec(
                filename="logo.png",
                height=256,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_small.png",
                height=128,
                redraw_manager=True,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_large.png",
                height=512,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_xlarge.png",
                height=1024,
                output_dir=assets_dir,
            ),
            # PDF report header logo
            ResizedLogoSpec(
                filename="logo_report.png",
                height=128,
                output_dir=report_assets_dir,
            ),
            # Documentation site and README preview image
            ResizedLogoSpec(
                filename="logo.png",
                height=400,
                output_dir=docs_images_dir,
            ),
            # Square icon elements in public directory
            ResizedLogoSpec(
                filename="favicon.png",
                is_square=True,
                square_size=32,
                output_dir=public_dir,
            ),
            ResizedLogoSpec(
                filename="apple-touch-icon.png",
                is_square=True,
                square_size=180,
                output_dir=public_dir,
            ),
        ],
    )

    resizer = LogoResizer(config)
    resizer.run()


if __name__ == "__main__":
    main()
