# Flask File Upload and Text Extraction Web App

This project is a Flask-based web application that allows users to upload image or PDF files, extract text from the uploaded files, and search the extracted text using the Whoosh search engine.

## Features

- **Upload files**: Supports image and PDF formats.
- **Text extraction**: Uses `pytesseract` for OCR on images and `pdfplumber` for extracting text from PDFs.
- **Search functionality**: Allows searching for keywords in the extracted text.
- **Multiple output formats**: The extracted text can be returned in plain text, JSON, or CSV format.

## Technologies Used

- **Flask**: Web framework.
- **Werkzeug**: For secure file handling.
- **pytesseract**: To perform OCR and extract text from images.
- **Pillow**: Image processing library.
- **pdfplumber**: For text extraction from PDF files.
- **Whoosh**: Full-text search and indexing library.

## Requirements

Ensure that the following are installed before running the project:

- Python 3.x
- Tesseract OCR (needed for `pytesseract`)
  
You can install the Python dependencies with:

```bash
pip install -r requirements.txt
