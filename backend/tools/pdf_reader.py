"""PDF reading and structured extraction."""

import logging
import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract full text from a PDF file."""
    logger.info("Reading PDF: %s", file_path)
    text_parts: list[str] = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception:
        logger.exception("Failed to read PDF: %s", file_path)
        raise
    return "\n\n".join(text_parts)


def extract_structured_info(text: str) -> dict[str, Any]:
    """Extract structured sections from academic paper text using heuristics."""
    sections = {
        "abstract": "",
        "methodology": "",
        "dataset": "",
        "results": "",
        "limitations": "",
        "conclusion": "",
        "full_text_preview": text[:3000],
    }

    section_patterns = {
        "abstract": r"(?i)(?:abstract)[:\s]*\n(.*?)(?=\n\s*(?:1\.?\s*)?(?:introduction|keywords|index terms|\n\n))",
        "methodology": r"(?i)(?:methodology|methods|approach|method)[:\s]*\n(.*?)(?=\n\s*(?:\d+\.?\s*)?(?:results|experiments|evaluation|\n\n))",
        "dataset": r"(?i)(?:dataset|data set|data)[:\s]*\n(.*?)(?=\n\s*(?:\d+\.?\s*)?(?:results|experiments|method|\n\n))",
        "results": r"(?i)(?:results|findings|evaluation|experiments)[:\s]*\n(.*?)(?=\n\s*(?:\d+\.?\s*)?(?:discussion|conclusion|limitations|\n\n))",
        "limitations": r"(?i)(?:limitations|limitation)[:\s]*\n(.*?)(?=\n\s*(?:\d+\.?\s*)?(?:conclusion|future|references|\n\n))",
        "conclusion": r"(?i)(?:conclusion|conclusions)[:\s]*\n(.*?)(?=\n\s*(?:\d+\.?\s*)?(?:references|acknowledgment|future|\n\n))",
    }

    for key, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            sections[key] = content[:2000]

    if not sections["abstract"]:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.match(r"(?i)^abstract", line.strip()):
                abstract_lines = []
                for j in range(i + 1, min(i + 20, len(lines))):
                    if re.match(r"(?i)^(introduction|keywords|1\.?\s)", lines[j].strip()):
                        break
                    abstract_lines.append(lines[j])
                sections["abstract"] = "\n".join(abstract_lines).strip()[:2000]
                break

    return sections


def read_pdf(file_path: str) -> dict[str, Any]:
    """Read a PDF and return text plus structured extraction."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    text = extract_text_from_pdf(file_path)
    structured = extract_structured_info(text)

    metadata: dict[str, Any] = {"filename": path.name, "page_count": 0, "char_count": len(text)}
    try:
        doc = fitz.open(file_path)
        metadata["page_count"] = doc.page_count
        if doc.metadata:
            metadata["title"] = doc.metadata.get("title", path.stem)
            metadata["author"] = doc.metadata.get("author", "")
        doc.close()
    except Exception:
        logger.warning("Could not extract PDF metadata")

    return {
        "text": text,
        "structured": structured,
        "metadata": metadata,
    }
