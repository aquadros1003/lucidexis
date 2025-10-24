import logging
from pathlib import Path
import pymupdf4llm


logger = logging.getLogger(__name__)


class Extractor:
    @staticmethod
    def extract_text(file_path: Path) -> str:
        raise NotImplementedError("Extractor is an abstract base class.")


class PDFExtractor(Extractor):
    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from PDF {file_path=}")
        text = ""
        try:
            doc = pymupdf4llm.to_markdown(file_path)
            logger.info(f"Successfully extracted text from PDF {file_path=}")
            return doc
        except Exception as e:
            logger.error(f"Error extracting text from PDF file {file_path=}: {e}")
        return text


class TxtExtractor(Extractor):
    @staticmethod
    def extract_text(file_path: Path) -> str:
        logger.info(f"Extracting text from TXT file: {file_path}")
        text = ""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
            logger.info(f"Successfully extracted text from TXT file: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting text from TXT file {file_path}: {e}")
        return text


EXTRACTOR_MAP: dict[str, Extractor] = {
    "application/pdf": PDFExtractor,
    "text/plain": TxtExtractor,
}
