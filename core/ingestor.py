import os
import tempfile
import requests
import validators
import pymupdf4llm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "chroma_db")

class DocumentIngestor:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def is_valid_url(self, url: str) -> bool:
        return validators.url(url)

    def download_pdf(self, url: str) -> str:
        """Download remote PDF to a temporary file and return the path."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(temp_file.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return temp_file.name

    def save_uploaded_file(self, uploaded_file) -> str:
        """Save a streamlit uploaded file to a temp file."""
        suffix = os.path.splitext(uploaded_file.name)[1]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        return temp_file.name

    def load_document(self, file_path: str) -> list[Document]:
        """Loads a file path into LangChain Documents."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            # Use PyMuPDF4LLM for high accuracy PDF parsing
            # It returns markdown representation by default
            # We can convert it to Langchain documents
            md_text = pymupdf4llm.to_markdown(file_path, write_images=False)
            
            # Since pymupdf4llm outputs a single markdown string, we can wrap it
            # To preserve page numbers, we would need to pass page_chunks=True
            docs_dicts = pymupdf4llm.to_markdown(file_path, page_chunks=True)
            
            lc_docs = []
            for doc in docs_dicts:
                metadata = {
                    "source": os.path.basename(file_path),
                    "page": doc.get("metadata", {}).get("page", 0) + 1
                }
                lc_docs.append(Document(page_content=doc["text"], metadata=metadata))
            return lc_docs
            
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
            return loader.load()
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def ingest(self, source, is_url=False) -> Chroma:
        """
        Ingests a document, splits it, and stores it in Chroma.
        Returns the initialized Chroma instance.
        """
        temp_path = None
        try:
            if is_url:
                if not self.is_valid_url(source):
                    raise ValueError("Invalid URL provided.")
                temp_path = self.download_pdf(source)
            else:
                # Assuming 'source' is a Streamlit UploadedFile
                temp_path = self.save_uploaded_file(source)

            documents = self.load_document(temp_path)
            
            # Add extra metadata for the source name
            source_name = source if is_url else source.name
            for doc in documents:
                doc.metadata["document_name"] = source_name

            split_docs = self.text_splitter.split_documents(documents)
            
            # Create/load Chroma DB
            vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIR
            )
            return vectorstore

        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
