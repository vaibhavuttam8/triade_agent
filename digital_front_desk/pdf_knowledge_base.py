import os
import re
import numpy as np
import faiss
from PyPDF2 import PdfReader
import openai
from typing import List, Dict, Any, Optional
from .telemetry import telemetry
from opentelemetry import trace
import time
import asyncio

class PDFKnowledgeBase:
    def __init__(self):
        self.client = None
        self.index = None
        self.chunks = []
        self.loaded = False
        self.pdf_path = os.getenv("ESI_GUIDELINES_PATH", "esi_guidelines.pdf")
        self.model_name = "text-embedding-ada-002"  # OpenAI embeddings model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_dimension = 1536  # Dimension for text-embedding-ada-002
        
    async def initialize(self) -> bool:
        """Initialize the knowledge base by loading the PDF and creating the embeddings index"""
        with telemetry.tracer.start_as_current_span("pdf_knowledge_base_init") as span:
            start_time = time.time()
            
            try:
                # Check for OpenAI API key
                if not self.api_key:
                    span.set_attributes({
                        "pdf.initialization_success": False,
                        "pdf.error": "OpenAI API key not found"
                    })
                    return False
                    
                # Configure OpenAI client
                self.client = openai.OpenAI(api_key=self.api_key)
                
                # Process PDF if it exists
                if os.path.exists(self.pdf_path):
                    # Extract and process the text from the PDF
                    data = self.extract_text_with_headings(self.pdf_path)
                    self.chunks = self.chunk_by_headings(data)
                    
                    # Generate embeddings
                    embeddings = await self.generate_embeddings(self.chunks)
                    
                    # Create FAISS index
                    self.index = self.store_in_faiss(embeddings)
                    self.loaded = True
                    
                    # Record metrics
                    processing_time = (time.time() - start_time) * 1000
                    telemetry.record_response_time(processing_time, "pdf_knowledge_base_init")
                    
                    span.set_attributes({
                        "pdf.chunks_count": len(self.chunks),
                        "pdf.model_name": self.model_name,
                        "pdf.processing_time_ms": processing_time,
                        "pdf.initialization_success": True
                    })
                    
                    return True
                else:
                    span.set_attributes({
                        "pdf.initialization_success": False,
                        "pdf.error": "PDF file not found"
                    })
                    
                    return False
                    
            except Exception as e:
                self.loaded = False
                span.set_attributes({
                    "pdf.initialization_success": False,
                    "pdf.error": str(e)
                })
                return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file"""
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def extract_text_with_headings(self, pdf_path: str) -> List[Dict[str, str]]:
        """Extract text from PDF, organizing by headings"""
        reader = PdfReader(pdf_path)
        data = []
        for page in reader.pages:
            text = page.extract_text()
            lines = text.split("\n")
            for line in lines:
                if re.match(r"^[A-Z][A-Z\s]+$", line.strip()):  # Detect uppercase headings
                    data.append({"heading": line.strip(), "content": ""})
                elif data:
                    data[-1]["content"] += line.strip() + " "
        return data
    
    def chunk_by_headings(self, data: List[Dict[str, str]], max_chunk_size: int = 500) -> List[str]:
        """Break content into smaller chunks based on headings"""
        chunks = []
        for section in data:
            heading = section["heading"]
            content = section["content"].split()
            for i in range(0, len(content), max_chunk_size):
                chunk = " ".join(content[i:i + max_chunk_size])
                chunks.append(f"{heading}\n{chunk}")
        return chunks
    
    async def generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Generate embeddings for text chunks using OpenAI API"""
        all_embeddings = []
        
        # Process chunks in batches to avoid rate limiting
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            try:
                # Call OpenAI embeddings API with new client syntax
                response = await asyncio.to_thread(
                    lambda: self.client.embeddings.create(
                        input=batch_chunks,
                        model=self.model_name
                    )
                )
                
                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Add a small delay to avoid rate limiting
                if i + batch_size < len(chunks):
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                # Log the error and continue with the next batch
                print(f"Error generating embeddings for batch {i}: {str(e)}")
                # Add zero embeddings for failed chunks to maintain alignment
                zero_embeddings = [np.zeros(self.embedding_dimension) for _ in range(len(batch_chunks))]
                all_embeddings.extend(zero_embeddings)
                
        return np.array(all_embeddings, dtype=np.float32)
    
    def store_in_faiss(self, embeddings: np.ndarray) -> faiss.IndexFlatIP:
        """Store embeddings in a FAISS index"""
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product similarity
        index.add(np.array(embeddings))
        return index
    
    async def query_knowledge_base(self, query: str, top_k: int = 3) -> List[str]:
        """Query the knowledge base to find relevant information based on a query"""
        with telemetry.tracer.start_as_current_span("query_knowledge_base") as span:
            start_time = time.time()
            
            if not self.loaded or not self.index:
                return ["Knowledge base not initialized."]
            
            try:
                # Generate embedding for the query using OpenAI API with new client syntax
                response = await asyncio.to_thread(
                    lambda: self.client.embeddings.create(
                        input=[query],
                        model=self.model_name
                    )
                )
                
                query_embedding = np.array([response.data[0].embedding], dtype=np.float32)
                
                # Search the index
                distances, indices = self.index.search(query_embedding, top_k)
                
                # Get the relevant chunks
                relevant_chunks = [self.chunks[i] for i in indices[0]]
                
                # Record metrics
                processing_time = (time.time() - start_time) * 1000
                telemetry.record_response_time(processing_time, "query_knowledge_base")
                
                span.set_attributes({
                    "query.processing_time_ms": processing_time,
                    "query.top_k": top_k,
                    "query.success": True
                })
                
                return relevant_chunks
                
            except Exception as e:
                span.set_attributes({
                    "query.success": False,
                    "query.error": str(e)
                })
                return []
    
    async def get_context_for_symptoms(self, symptoms: str) -> str:
        """Get relevant ESI guidelines context based on patient symptoms"""
        if not self.loaded:
            return ""
            
        # Create a more focused query based on the symptoms
        query = f"ESI triage guidelines for patient with {symptoms}"
        
        # Get relevant chunks
        relevant_chunks = await self.query_knowledge_base(query)
        
        # Combine the chunks into a single context string
        context = "\n\n".join(relevant_chunks)
        
        return context

# Create global instance
pdf_knowledge_base = PDFKnowledgeBase() 