import csv
import fitz  # PyMuPDF
import json
import yaml
from io import BytesIO, StringIO
import pandas as pd
 
def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return {"context":text.strip(),"message":"PDF content extracted successfully"}
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        file_stream = BytesIO(file_bytes)
        doc = Document(file_stream)
        return {"context":"\n".join(para.text for para in doc.paragraphs).strip(),"message":"Doc file content extracted successfully"}
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {e}")


def extract_text_from_json(file_bytes: bytes) -> str:
    try:
        data = json.loads(file_bytes.decode("utf-8"))
        return {"context":json.dumps(data, indent=2),"message":"JSON data extracted successfully"}
    except Exception as e:
        raise ValueError(f"Failed to extract text from JSON: {e}")


def extract_text_from_yaml(file_bytes: bytes) -> str:
    try:
        data = yaml.safe_load(file_bytes.decode("utf-8"))
        return {"context":yaml.dump(data, default_flow_style=False),"message":"YAML data extracted successfully"}
    except Exception as e:
        raise ValueError(f"Failed to extract text from YAML: {e}")

def extract_text_from_csv(file_bytes: bytes) -> dict:
    try:
        csv_text = file_bytes.decode("utf-8")
        reader = csv.reader(StringIO(csv_text))
        rows = [" | ".join(row) for row in reader]
        return {
            "context": "\n".join(rows),
            "message": "CSV data extracted successfully"
        }
    except Exception as e:
        raise ValueError(f"Failed to extract text from CSV: {e}")

def extract_text_from_excel(file_bytes: bytes) -> dict:
    """
    Reads all sheets from an Excel file and extracts text in a human-readable format.
    Useful for sending to LLMs.
    """
    try:
        # Read all sheets into a dict of DataFrames
        sheets = pd.read_excel(BytesIO(file_bytes), sheet_name=None)

        all_text = []
        for sheet_name, df in sheets.items():
            df = df.fillna("")  # Replace NaN with empty strings
            sheet_text = f"### Sheet: {sheet_name}\n"

            for _, row in df.iterrows():
                row_text = " | ".join(str(cell).strip() for cell in row if str(cell).strip())
                if row_text:
                    sheet_text += row_text + "\n"

            all_text.append(sheet_text.strip())

        full_text = "\n\n".join(all_text).strip()

        return {
            "context": full_text,
            "message": "Excel content extracted successfully",
        }

    except Exception as e:
        raise ValueError(f"Failed to extract text from Excel: {e}")

def extract_text_from_plain_text(file_bytes: bytes) -> str:
    try:
        text = file_bytes.decode("utf-8")
        return {"context":text.strip(),"message":"Plain text content extracted successfully"}
    except Exception as e:
        raise ValueError(f"Failed to extract text from plain text file: {e}")
