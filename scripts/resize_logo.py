#!/usr/bin/env python3
"""Script to automatically resize the original logo into optimized web assets.

Reads the high-resolution source logo, removes any checkerboard background patterns,
generates both light-mode and dark-mode versions, and outputs standard size variations.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path
from PIL import Image
from loguru import logger
from pydantic import BaseModel, Field


class ResizedLogoSpec(BaseModel):
    """Specification for a resized logo image output configuration.

    Attributes:
        filename (str): Name of the generated output file.
        height (int | None): Target height in pixels for aspect-ratio preservation.
        is_square (bool): True if image should be centered and padded on a square canvas.
        square_size (int | None): Size of the square canvas in pixels.
        is_dark_mode (bool): True if dark colors should be converted to white for dark mode contrast.
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
    is_dark_mode: bool = Field(
        default=False,
        description="True if output should be adjusted for dark mode contrast.",
    )
    output_dir: Path = Field(description="Output target directory.")


class LogoResizerConfig(BaseModel):
    """Configuration for the logo resizer process.

    Attributes:
        source_light_path (Path): Path to the light-mode high-resolution source logo.
        source_dark_path (Path): Path to the dark-mode high-resolution source logo.
        specs (list[ResizedLogoSpec]): List of image specifications to generate.
    """

    model_config = {"extra": "forbid"}

    source_light_path: Path = Field(
        description="Path to the light-mode source logo file."
    )
    source_dark_path: Path = Field(
        description="Path to the dark-mode source logo file."
    )
    specs: list[ResizedLogoSpec] = Field(description="List of target specifications.")


class LogoResizer:
    """A tool for generating optimized, resized images from a source logo.

    Handles checkerboard background removal, dark mode color conversion,
    aspect-ratio resizing, and square padded icon generation.
    """

    def __init__(self, config: LogoResizerConfig) -> None:
        """Initialize the resizer with configuration.

        Args:
            config (LogoResizerConfig): The configuration containing source paths and specs.
        """
        self.config = config

    def _remove_checkerboard_background(self, img: Image.Image) -> Image.Image:
        """Remove a white/grey checkerboard background starting from the edges.

        Uses a BFS traversal to find all connected background-like pixels and
        converts them to transparent.

        Args:
            img (Image.Image): The source PIL image object.

        Returns:
            Image.Image: The PIL image object with checkerboard background removed.
        """
        logger.info("Detecting and removing checkerboard background...")
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()

        visited = set()

        def is_bg_pixel(x: int, y: int) -> bool:
            r, g, b, a = pixels[x, y]
            # White checkerboard squares
            if r > 230 and g > 230 and b > 230:
                return True
            # Grey checkerboard squares
            if 180 < r < 220 and 180 < g < 220 and 180 < b < 220:
                if max(r, g, b) - min(r, g, b) < 15:
                    return True
            return False

        # Queue for BFS
        queue = deque()

        # Add all border pixels to the queue to seed BFS
        for x in range(width):
            for y in [0, height - 1]:
                if is_bg_pixel(x, y):
                    queue.append((x, y))
                    visited.add((x, y))
        for y in range(height):
            for x in [0, width - 1]:
                if (x, y) not in visited and is_bg_pixel(x, y):
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

    def _convert_for_dark_mode(self, img: Image.Image) -> Image.Image:
        """Convert dark colors in the logo to white for better dark mode visibility.

        Leaves accent colors intact by only targeting dark colors (max RGB < 150).

        Args:
            img (Image.Image): The transparent PIL image object.

        Returns:
            Image.Image: The dark-mode adjusted PIL image object.
        """
        logger.info("Converting dark logo components to white for dark mode...")
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()
        res = img.copy()
        res_pixels = res.load()

        converted_count = 0
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    # Target dark colors (like navy blue and near-black)
                    if max(r, g, b) < 150:
                        res_pixels[x, y] = (255, 255, 255, a)
                        converted_count += 1

        logger.info(
            f"Dark mode conversion complete. Converted {converted_count} pixels to white."
        )
        return res

    def _resize_aspect_ratio(self, img: Image.Image, target_height: int) -> Image.Image:
        """Resize the image to a target height while preserving aspect ratio.

        Args:
            img (Image.Image): The source PIL image object.
            target_height (int): The target height in pixels.

        Returns:
            Image.Image: The resized PIL image object.
        """
        w, h = img.size
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

        source_path = (
            self.config.source_dark_path
            if spec.is_dark_mode
            else self.config.source_light_path
        )

        with Image.open(source_path) as raw_img:
            # Clean background transparency
            img = self._remove_checkerboard_background(raw_img)

            # Apply dark mode conversion if specified and using the light source as fallback
            if spec.is_dark_mode and source_path == self.config.source_light_path:
                img = self._convert_for_dark_mode(img)

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
                processed_img = self._resize_aspect_ratio(img, spec.height)

            # Save the image with PNG optimization
            processed_img.save(dest_path, "PNG", optimize=True)
            logger.info(f"Successfully saved optimized image to {dest_path}")

    def run(self) -> None:
        """Execute the resizing process for all specifications in the configuration."""
        logger.info(
            f"Starting logo resizing process for sources: "
            f"{self.config.source_light_path} and {self.config.source_dark_path}"
        )
        for spec in self.config.specs:
            self.process_spec(spec)
        logger.info("Logo resizing process completed successfully.")


def main() -> None:
    """Main entry point to execute the logo resizing script."""
    root_dir = Path(__file__).resolve().parent.parent
    source_light = root_dir / "frontend/src/assets/logo_light_original.png"
    source_dark = root_dir / "frontend/src/assets/logo_dark_original.png"
    assets_dir = root_dir / "frontend/src/assets"
    public_dir = root_dir / "frontend/public"

    if not source_light.exists():
        logger.error(f"Source light logo not found at: {source_light}")
        sys.exit(1)

    if not source_dark.exists():
        logger.error(f"Source dark logo not found at: {source_dark}")
        sys.exit(1)

    config = LogoResizerConfig(
        source_light_path=source_light,
        source_dark_path=source_dark,
        specs=[
            # Light Mode Logos
            ResizedLogoSpec(
                filename="logo.png",
                height=256,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_small.png",
                height=64,
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
            # Dark Mode Logos
            ResizedLogoSpec(
                filename="logo_dark.png",
                height=256,
                is_dark_mode=True,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_dark_small.png",
                height=64,
                is_dark_mode=True,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_dark_large.png",
                height=512,
                is_dark_mode=True,
                output_dir=assets_dir,
            ),
            ResizedLogoSpec(
                filename="logo_dark_xlarge.png",
                height=1024,
                is_dark_mode=True,
                output_dir=assets_dir,
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
