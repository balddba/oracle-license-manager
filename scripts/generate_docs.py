#!/usr/bin/env python3
"""Script for building and serving Oracle License Manager documentation.

Supports dependency verification, site directory cleaning, static site building,
and running a local development server for previewing changes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field


class DocConfig(BaseModel):
    """Configuration options for documentation generation.

    Attributes:
        clean (bool): If True, removes the build directory before building.
        serve (bool): If True, starts a local development server.
        host (str): Bind address for the development server.
        port (int): Port to run the development server on.
        strict (bool): If True, treats mkdocs warnings as errors.
        site_dir (Path): Output directory for static HTML.
        config_path (Path): Path to the mkdocs.yml file.
    """

    model_config = {"extra": "forbid"}

    clean: bool = False
    serve: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    strict: bool = False
    site_dir: Path = Field(
        default=Path("site"), description="Output directory for HTML."
    )
    config_path: Path = Field(
        default=Path("mkdocs.yml"), description="Path to configuration."
    )


class DocGenerator:
    """Handles verification of dependencies, cleaning, building, and serving the documentation."""

    def __init__(self, config: DocConfig) -> None:
        """Initialize the generator with configuration.

        Args:
            config (DocConfig): The configuration settings.
        """
        self.config = config

    def _get_env(self) -> dict[str, str]:
        """Get the environment variables for running subprocesses.

        Ensures Homebrew library path is added to DYLD_FALLBACK_LIBRARY_PATH on macOS
        so that Cairo libraries can be successfully loaded for the social plugin.

        Returns:
            dict[str, str]: The environment variables dictionary.
        """
        env = os.environ.copy()
        if sys.platform == "darwin":
            brew_lib = "/opt/homebrew/lib"
            if os.path.exists(brew_lib):
                fallback = env.get("DYLD_FALLBACK_LIBRARY_PATH", "")
                env["DYLD_FALLBACK_LIBRARY_PATH"] = (
                    f"{brew_lib}:{fallback}" if fallback else brew_lib
                )
        return env

    def _ensure_dependencies(self) -> None:
        """Ensure that mkdocs and required plugins are installed.

        Raises:
            RuntimeError: If dependencies are missing and cannot be installed.
        """
        logger.info("Verifying documentation dependencies...")
        try:
            import mkdocs  # noqa: F401

            logger.info("Found mkdocs installation.")
        except ImportError:
            logger.warning("mkdocs is not installed in the current environment.")
            self._install_dependencies()

    def _install_dependencies(self) -> None:
        """Install required doc dependencies using uv or pip.

        Raises:
            RuntimeError: If the package installation command fails.
        """
        logger.info("Attempting to install missing documentation dependencies...")

        if shutil.which("uv"):
            cmd = ["uv", "sync", "--extra", "docs"]
            logger.info(f"Running installation command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(
                    f"Failed to sync docs dependencies via uv: {result.stderr}"
                )
                raise RuntimeError("Could not install documentation dependencies.")
        else:
            cmd = [sys.executable, "-m", "pip", "install", "mkdocs", "mkdocs-material"]
            logger.info(f"Running installation command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(
                    f"Failed to install docs dependencies via pip: {result.stderr}"
                )
                raise RuntimeError("Could not install documentation dependencies.")
        logger.info("Documentation dependencies installed successfully.")

    def clean(self) -> None:
        """Remove the generated documentation output directory."""
        if self.config.site_dir.exists():
            logger.info(
                f"Cleaning existing documentation build directory: {self.config.site_dir}"
            )
            try:
                shutil.rmtree(self.config.site_dir)
                logger.info("Clean completed successfully.")
            except Exception as e:
                logger.error(f"Failed to clean site directory: {e}")
                raise
        else:
            logger.info("Build directory does not exist. Skipping clean.")

    def build(self) -> None:
        """Build the static HTML documentation using mkdocs.

        Raises:
            RuntimeError: If the build command fails.
        """
        self._ensure_dependencies()
        if self.config.clean:
            self.clean()

        logger.info(f"Building static documentation from {self.config.config_path}...")
        cmd = ["mkdocs", "build", "-f", str(self.config.config_path)]
        if self.config.strict:
            cmd.append("--strict")

        if shutil.which("uv"):
            cmd = ["uv", "run"] + cmd

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=self._get_env())
        if result.returncode != 0:
            raise RuntimeError(
                f"mkdocs build failed with exit code {result.returncode}"
            )
        logger.info(f"Documentation successfully built to {self.config.site_dir}/")

    def serve(self) -> None:
        """Start the mkdocs development server.

        Raises:
            RuntimeError: If the server fails to start or run.
        """
        self._ensure_dependencies()

        logger.info(
            f"Starting mkdocs development server on http://{self.config.host}:{self.config.port}..."
        )
        cmd = [
            "mkdocs",
            "serve",
            "-f",
            str(self.config.config_path),
            "-a",
            f"{self.config.host}:{self.config.port}",
        ]

        if shutil.which("uv"):
            cmd = ["uv", "run"] + cmd

        logger.info(f"Running command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, env=self._get_env())
        except KeyboardInterrupt:
            logger.info("Development server stopped by user.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"mkdocs serve failed with exit code {e.returncode}")


def main() -> None:
    """Parse command line arguments and execute the corresponding documentation action."""
    parser = argparse.ArgumentParser(
        description="Helper script to build and serve project documentation."
    )
    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="Remove build directory before building.",
    )
    parser.add_argument(
        "-s",
        "--serve",
        action="store_true",
        help="Start development server after/instead of building.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind dev server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to run dev server on (default: 8000).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (treat warnings as build errors).",
    )

    args = parser.parse_args()

    config = DocConfig(
        clean=args.clean,
        serve=args.serve,
        host=args.host,
        port=args.port,
        strict=args.strict,
    )

    generator = DocGenerator(config)

    try:
        if config.serve:
            generator.serve()
        else:
            generator.build()
    except Exception as e:
        logger.error(f"Documentation command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
