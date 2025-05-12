from langchain_community.document_loaders import PyPDFLoader, DocxLoader, CSVLoader


def load_document(file_path: str):
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = DocxLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path)
    else:
        raise ValueError("Не поддерживаемый формат файла")

    return loader.load()