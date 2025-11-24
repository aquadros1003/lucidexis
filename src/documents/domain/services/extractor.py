import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import pymupdf4llm  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    pass


class Extractor(ABC):
    @staticmethod
    @abstractmethod
    def extract_text(file_path: Path) -> str:
        pass

    @staticmethod
    def _read_file(file_path: Path, encoding: str = "utf-8") -> str:
        try:
            with open(file_path, encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as file:
                    return file.read()
            except Exception as e:
                raise ExtractionError(
                    f"Failed to read file {file_path} with any encoding: {e}"
                )
        except Exception as e:
            raise ExtractionError(f"Failed to read file {file_path}: {e}")


class PDFExtractor(Extractor):
    """Extractor for PDF files using pymupdf4llm."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from PDF {file_path=}")
        try:
            text: str = pymupdf4llm.to_markdown(file_path, table_strategy="lines_strict")
            text = text.replace("<br>", " ")
            logger.info(f"Successfully extracted text from PDF {file_path=}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF file {file_path=}: {e}")
            raise ExtractionError(f"PDF extraction failed for {file_path}: {e}")


class TxtExtractor(Extractor):
    """Extractor for plain text files."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from TXT file: {file_path}")
        try:
            text = Extractor._read_file(file_path)
            logger.info(f"Successfully extracted text from TXT file: {file_path}")
            return text
        except ExtractionError as e:
            logger.error(f"Error extracting text from TXT file {file_path}: {e}")
            raise


class MarkdownExtractor(Extractor):
    """Extractor for Markdown files."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from Markdown file: {file_path}")
        try:
            text = Extractor._read_file(file_path)
            logger.info(f"Successfully extracted text from Markdown file: {file_path}")
            return text
        except ExtractionError as e:
            logger.error(f"Error extracting text from Markdown file {file_path}: {e}")
            raise


class HTMLExtractor(Extractor):
    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from HTML file: {file_path}")
        try:
            html_content = Extractor._read_file(file_path)
            text = re.sub(
                r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL
            )
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            logger.info(f"Successfully extracted text from HTML file: {file_path}")
            return text
        except ExtractionError as e:
            logger.error(f"Error extracting text from HTML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing HTML file {file_path}: {e}")
            raise ExtractionError(f"HTML extraction failed for {file_path}: {e}")


class JSONExtractor(Extractor):
    """Extractor for JSON files."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from JSON file: {file_path}")
        try:
            json_content = Extractor._read_file(file_path)
            data = json.loads(json_content)
            text = json.dumps(data, indent=2, ensure_ascii=False)
            logger.info(f"Successfully extracted text from JSON file: {file_path}")
            return text
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise ExtractionError(f"Invalid JSON in {file_path}: {e}")
        except ExtractionError as e:
            logger.error(f"Error extracting text from JSON file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {e}")
            raise ExtractionError(f"JSON extraction failed for {file_path}: {e}")


class CSVExtractor(Extractor):
    """Extractor for CSV files."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from CSV file: {file_path}")
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
            df.fillna("", inplace=True)
            text = df.to_markdown(index=False, tablefmt="github")
            text = text.replace("\r", " ")
            logger.info(f"Successfully extracted text from CSV file: {file_path}")
            return text
        except pd.errors.EmptyDataError as e:
            logger.error(f"Empty CSV file {file_path}: {e}")
            raise ExtractionError(f"Empty CSV file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            raise ExtractionError(f"CSV extraction failed for {file_path}: {e}")


class XMLExtractor(Extractor):
    """Extractor for XML files."""

    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from XML file: {file_path}")
        try:
            xml_content = Extractor._read_file(file_path)
            text = re.sub(r"<[^>]+>", " ", xml_content)
            text = re.sub(r"\s+", " ", text).strip()
            logger.info(f"Successfully extracted text from XML file: {file_path}")
            return text
        except ExtractionError as e:
            logger.error(f"Error extracting text from XML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing XML file {file_path}: {e}")
            raise ExtractionError(f"XML extraction failed for {file_path}: {e}")


class ExtractorRegistry:
    """Registry for managing document extractors."""

    def __init__(self) -> None:
        self._extractors: dict[str, type[Extractor]] = {}

    def register(self, mime_type: str, extractor: type[Extractor]) -> None:
        self._extractors[mime_type] = extractor
        logger.debug(f"Registered extractor {extractor.__name__} for {mime_type}")

    def get_extractor(self, mime_type: str) -> type[Extractor] | None:
        return self._extractors.get(mime_type)

    def is_supported(self, mime_type: str) -> bool:
        return mime_type in self._extractors

    def get_supported_types(self) -> list[str]:
        return list(self._extractors.keys())


# Create global registry and register extractors
_registry = ExtractorRegistry()
_registry.register("application/pdf", PDFExtractor)
_registry.register("text/plain", TxtExtractor)
_registry.register("text/markdown", MarkdownExtractor)
_registry.register("text/html", HTMLExtractor)
_registry.register("application/json", JSONExtractor)
_registry.register("text/csv", CSVExtractor)
_registry.register("text/xml", XMLExtractor)
_registry.register("application/xml", XMLExtractor)

# Backward compatibility
EXTRACTOR_MAP: dict[str, type[Extractor]] = {
    mime_type: _registry.get_extractor(mime_type)  # type: ignore
    for mime_type in _registry.get_supported_types()
}
