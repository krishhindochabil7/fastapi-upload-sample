import fitz  # PyMuPDF
import csv
from io import BytesIO
from typing import List
from langchain.docstore.document import Document
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.text_splitter import TokenTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
import os

# Directly assign secret key values here
GROQ_API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyBuAuw3GZQ5xGxf651tgWi6mguatIdmc_4"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "kh27042001"

# Initialize API clients
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
llm = ChatGroq(
    model="mixtral-8x7b-32768",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)  # Initialize ChatGroq with specified parameters

graph = None
final_documents = None

def loading_graph(file_stream: BytesIO, file_name: str):
    global graph
    global final_documents
    final_documents = []

    def load_file(file_stream: BytesIO, file_name: str):
        all_documents = []
        file_count = 0  # Initialize the file counter
        
        # Debug print for file type
        print(f"Processing file: {file_name}")

        try:
            if file_name.endswith(".pdf"):
                # Process PDF
                file_stream.seek(0)  # Ensure we're at the beginning of the stream
                pdf_document = fitz.open(stream=file_stream.read(), filetype="pdf")
                successful_pages = 0
                for page_number in range(len(pdf_document)):
                    page = pdf_document.load_page(page_number)
                    text = page.get_text()
                    if text.strip():
                        all_documents.append(Document(page_content=text, metadata={"source": file_name, "page_number": page_number}))
                        successful_pages += 1
                if successful_pages > 0:
                    file_count += 1
            elif file_name.endswith(".csv"):
                # Process CSV
                file_stream.seek(0)  # Ensure we're at the beginning of the stream
                csv_content = file_stream.read().decode('utf-8')
                reader = csv.reader(csv_content.splitlines())
                content = ""
                for row in reader:
                    content += " ".join(row) + "\n"
                if content.strip():
                    all_documents.append(Document(page_content=content, metadata={"source": file_name}))
                    file_count += 1
            else:
                raise ValueError("Unsupported file type.")
        except Exception as e:
            print(f"An error occurred while processing {file_name}: {e}")

        return all_documents

    documents = load_file(file_stream, "uploaded_file")
    if documents is not None and len(documents) > 0:
        answer = "File uploaded successfully!"
    else:
        answer = "Error processing file. Please check input path and try again. Thank you!"

    os.environ["NEO4J_URI"] = NEO4J_URI
    os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
    os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD

    graph = Neo4jGraph()
    text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
    final_documents = text_splitter.split_documents(documents)

    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(final_documents)

    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )
    
    print("Graph loading completed.")
    return answer
