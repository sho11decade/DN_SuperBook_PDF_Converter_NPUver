#!/usr/bin/env python3
import argparse
import importlib.util
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Any

LOG = logging.getLogger("convertpdf")


def detect_backend() -> str:
    """Detect NPU availability based on OpenVINO module presence (placeholder check)."""
    for module_name in ("openvino.runtime", "openvino"):
        try:
            spec = importlib.util.find_spec(module_name)
        except ModuleNotFoundError:
            spec = None
        if spec is not None:
            return "NPU"
    return "CPU"


def load_config(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Config file not found: {path}") from exc
    except PermissionError as exc:
        raise RuntimeError(f"Config file not readable: {path}") from exc
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is not installed; cannot read YAML config.") from exc
        return yaml.safe_load(text) or {}
    try:
        return json.loads(text) or {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON config: {exc}") from exc


def collect_pdfs(inputs: list[str], recursive: bool) -> list[tuple[Path, Path]]:
    collected: list[tuple[Path, Path]] = []
    for raw in inputs:
        path = Path(raw)
        if not path.exists():
            LOG.error("Input not found: %s", path)
            continue
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            found = False
            for candidate in path.glob(pattern):
                if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                    collected.append((candidate, path))
                    found = True
            if not found:
                LOG.warning("No PDF files found in %s", path)
        else:
            if path.suffix.lower() != ".pdf":
                LOG.warning("Skipping non-PDF input: %s", path)
                continue
            collected.append((path, path.parent))
    return collected


def write_ocr_placeholders(output_pdf: Path, source_pdf: Path) -> None:
    ocr_pdf = output_pdf.with_name(f"{output_pdf.stem}.ocr.pdf")
    if ocr_pdf.exists():
        ocr_pdf.unlink()
    shutil.copy2(output_pdf, ocr_pdf)

    html_path = output_pdf.with_suffix(".html")
    md_path = output_pdf.with_suffix(".md")
    json_path = output_pdf.with_suffix(".json")

    html_path.write_text(
        f"<html><body><h1>OCR placeholder</h1><p>Source: {source_pdf}</p></body></html>\n",
        encoding="utf-8",
    )
    md_path.write_text(
        f"# OCR placeholder\n\nSource: {source_pdf}\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps({"source": str(source_pdf), "status": "placeholder"}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def merge_setting(cli_value: Any, config: dict, key: str, default: Any) -> Any:
    """Return the CLI value if set, otherwise config value, otherwise default."""
    if cli_value is not None:
        return cli_value
    return config.get(key, default)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="convertpdf",
        description="Minimal PDF converter skeleton (NPU/CPU placeholder)",
    )
    parser.add_argument("inputs", nargs="+", help="PDF files or directories")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory")
    parser.add_argument(
        "-r",
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Recurse into directories",
    )
    parser.add_argument(
        "--ocr",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Emit OCR placeholder outputs",
    )
    parser.add_argument("--config", help="Config file (JSON/YAML)")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    config: dict = {}
    if args.config:
        try:
            config = load_config(Path(args.config))
        except (OSError, RuntimeError) as exc:
            LOG.error("Failed to load config: %s", exc)
            return 1

    output_dir = Path(merge_setting(args.output_dir, config, "output_dir", "output"))
    recursive = merge_setting(args.recursive, config, "recursive", False)
    ocr = merge_setting(args.ocr, config, "ocr", False)

    backend = detect_backend()
    if backend == "NPU":
        LOG.info("OpenVINO detected; using NPU backend (placeholder).")
    else:
        LOG.warning("OpenVINO not detected; using CPU fallback.")

    pdfs = collect_pdfs(args.inputs, recursive)
    if not pdfs:
        LOG.error("No PDF inputs to process.")
        return 1

    for pdf_path, base_dir in pdfs:
        try:
            relative = pdf_path.relative_to(base_dir)
        except ValueError:
            # Fallback for unexpected path relationships (e.g., symlinks).
            relative = Path(f"{pdf_path.stem}_{abs(hash(str(pdf_path)))}{pdf_path.suffix}")
        output_path = output_dir / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, output_path)
        LOG.info("Wrote PDF: %s", output_path)

        if ocr:
            write_ocr_placeholders(output_path, pdf_path)
            LOG.info("Wrote OCR placeholders for: %s", output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
