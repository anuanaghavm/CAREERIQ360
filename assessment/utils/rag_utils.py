# rag_utils.py
import os
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstores")

def get_vectorstore_path(theory_id):
    return os.path.join(VECTORSTORE_DIR, f"theory_{theory_id}_index")

def load_or_create_vectorstore(theory_id, theory_text):
    vectorstore_path = get_vectorstore_path(theory_id)

    if os.path.exists(vectorstore_path):
        db = FAISS.load_local(vectorstore_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    else:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents([Document(page_content=theory_text)])
        db = FAISS.from_documents(chunks, OpenAIEmbeddings())
        db.save_local(vectorstore_path)

    return db
