"""
File reader
"""

import os
from pathlib import Path
from typing import Optional
import PyPDF2
from docx import Document

class ResumeReader:
    """Interface for reading resume formats"""

    supported_formats = ['.pdf', '.docx', '.txt']

    def read_file(file_path):
        """
        Read a file and return its text content

        Args:
            file_path: Path to the resume file

        returns:
            Extracted text content or None if failed
        """

        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None

        extension = file_path.suffix.lower()
        if extension not in ResumeReader.supported_formats:
            print(f" Unsupported format: {extension}")
            print(f"Supported formats: {', '.join(ResumeReader.supported_formats)}")
            return None

        try:
            if extension == '.txt':
                return ResumeReader.read_txt(file_path)
            elif extension == '.docx':
                return ResumeReader.read_docx(file_path)
            elif extension == '.pdf':
                return ResumeReader.read_pdf(file_path)
        except Exception as e:
            print(f'Error reading {file_path.name}: {e}')
            return None 

    def read_txt(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as txt_file:
            text = txt_file.read()
        print(f"Read TXT: {file_path.name} with ({len(text)} of characters to process)")
        return text

    def read_docx(file_path):
        doc = Document(file_path)
        text_doc = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_doc.append(paragraph.text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_doc.append(cell.text)

        text = '\n'.join(text_doc)
        print(f"Read docx: {file_path.name} with ({len(text)}) of characters to process")
        return text

    def read_pdf(file_path):
        text_parts = []
        with open(file_path, 'rb') as file_pdf:
            pdf_reader = PyPDF2.PdfReader(file_pdf)
            num_pages = len(pdf_reader.pages)
            for pages in range(num_pages):
                page = pdf_reader.pages[pages]
                text_pdf = page.extract_text()
                if text_pdf.strip():
                    text_parts.append(text_pdf)
        full_text = '\n'.join(text_parts)
        print(f"Read PDF: {file_path.name} with ({len(full_text)} of characters ready to process from {num_pages} pages)")
        return full_text

    def get_file_information(file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return {"Error": "File Not Found"}
        return {
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "supported": file_path.suffix.lower() in ResumeReader.supported_formats
            }
