import os
import pandas as pd
from docx import Document as DocxReader
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from langchain.schema import Document as LangDocument


def load_document(file_path: str):
    """
    Загружает документ в список LangDocument.
    Поддержка PDF, CSV, DOCX, XLSX, XLS.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return PyPDFLoader(file_path).load()
    elif ext == '.csv':
        return CSVLoader(file_path).load()
    elif ext in ('.xlsx', '.xls'):
        engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        sheets = pd.read_excel(file_path, sheet_name=None, engine=engine)
        docs = []
        for sheet_name, df in sheets.items():
            rows = df.fillna('').astype(str).values.tolist()
            text = f"Sheet: {sheet_name}\n" + '\n'.join(['\t'.join(row) for row in rows])
            docs.append(LangDocument(page_content=text, metadata={'source':os.path.basename(file_path),'sheet':sheet_name}))
        return docs
    elif ext == '.docx':
        doc = DocxReader(file_path)
        text = '\n'.join([p.text for p in doc.paragraphs if p.text])
        return [LangDocument(page_content=text, metadata={'source':os.path.basename(file_path)})]
    else:
        raise ValueError(f"Не поддерживаемый формат: {ext}")