import os
import hashlib
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# Global cache for embeddings model
_embeddings_model = None

class DocumentProcessor:
    def __init__(self, groq_api_key=None):
        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not provided or set in environment")
        os.environ["GROQ_API_KEY"] = self.api_key

        self.embeddings = self._initialize_embeddings()
        self.llm = self._initialize_llm()
        self.vector_store_dir = os.path.join(os.path.dirname(__file__), '../../vector_stores')
        os.makedirs(self.vector_store_dir, exist_ok=True)

    def _initialize_embeddings(self):
        global _embeddings_model
        if _embeddings_model is None:
            print("Initializing embeddings model...")
            _embeddings_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        return _embeddings_model

    def _initialize_llm(self):
        return ChatGroq(
            model_name="llama-3.3-70b-versatile", 
            temperature=0.1
        )

    def get_document_hash(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def process_pdf(self, pdf_path):
        reader = PdfReader(pdf_path)
        raw_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text
        return raw_text

    def split_text(self, text):
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        return splitter.split_text(text)

    def embed_pdf(self, pdf_path, filename):
        """Process PDF and return FAISS vector store"""
        raw_text = self.process_pdf(pdf_path)
        chunks = self.split_text(raw_text)
        return self.create_vector_store(chunks)

    def create_vector_store(self, chunks):
        """Create vector store from existing text chunks"""
        return FAISS.from_texts(chunks, self.embeddings)