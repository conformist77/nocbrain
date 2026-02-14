"""
NOCbRAIN Knowledge Manager
RAG (Retrieval-Augmented Generation) implementation using LangChain and Qdrant
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import yaml

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NetworkKnowledgeSchema:
    """Schema for network knowledge classification"""
    
    KNOWLEDGE_TYPES = {
        "cisco_config": {
            "description": "Cisco device configuration files",
            "patterns": [
                "interface GigabitEthernet",
                "router ospf",
                "access-list",
                "vlan",
                "spanning-tree"
            ],
            "metadata_fields": ["device_type", "version", "hostname", "interfaces"]
        },
        "proxmox_log": {
            "description": "Proxmox virtualization platform logs",
            "patterns": [
                "pve-manager",
                "qemu",
                "lxc",
                "storage",
                "network"
            ],
            "metadata_fields": ["vm_id", "node", "action", "timestamp"]
        },
        "zabbix_data": {
            "description": "Zabbix monitoring data and alerts",
            "patterns": [
                "zabbix_server",
                "trigger",
                "item",
                "host",
                "problem"
            ],
            "metadata_fields": ["host", "item_key", "severity", "trigger_id"]
        },
        "security_event": {
            "description": "Security events and SIEM data",
            "patterns": [
                "failed login",
                "brute force",
                "lateral movement",
                "malware",
                "intrusion"
            ],
            "metadata_fields": ["source_ip", "target", "event_type", "severity"]
        },
        "network_topology": {
            "description": "Network topology and routing information",
            "patterns": [
                "routing table",
                "bgp",
                "ospf",
                "eigrp",
                "subnet"
            ],
            "metadata_fields": ["protocol", "network", "next_hop", "metric"]
        },
        "incident_report": {
            "description": "Historical incident reports and resolutions",
            "patterns": [
                "incident",
                "resolution",
                "root cause",
                "impact",
                "timeline"
            ],
            "metadata_fields": ["incident_id", "severity", "resolution_time", "affected_systems"]
        }
    }
    
    @classmethod
    def classify_content(cls, content: str, filename: str = "") -> str:
        """Classify content based on patterns and metadata"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        for knowledge_type, config in cls.KNOWLEDGE_TYPES.items():
            # Check filename patterns
            if any(pattern in filename_lower for pattern in config["patterns"]):
                return knowledge_type
            
            # Check content patterns
            if any(pattern in content_lower for pattern in config["patterns"]):
                return knowledge_type
        
        return "general"


class KnowledgeManager:
    """Main knowledge management service"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        
        # Initialize LangChain vector store
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name="nocbrain_knowledge",
            embeddings=self.embeddings
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Knowledge base path
        self.knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        
        # Collection name
        self.collection_name = "nocbrain_knowledge"
        
        logger.info("Knowledge Manager initialized")
    
    async def initialize_collection(self):
        """Initialize Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections
            )
            
            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    async def index_knowledge_base(self, force_reindex: bool = False) -> Dict[str, Any]:
        """Index the entire knowledge base into Qdrant"""
        try:
            await self.initialize_collection()
            
            # Get existing documents count
            existing_count = self.qdrant_client.count(
                collection_name=self.collection_name
            ).count
            
            if force_reindex:
                logger.info("Force reindexing - clearing existing collection")
                self.qdrant_client.delete_collection(self.collection_name)
                await self.initialize_collection()
                existing_count = 0
            
            # Process knowledge base files
            indexed_files = 0
            total_chunks = 0
            
            for file_path in self.knowledge_base_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.log', '.conf', '.yaml', '.yml', '.json']:
                    try:
                        result = await self.index_file(file_path)
                        indexed_files += 1
                        total_chunks += result['chunks']
                        logger.info(f"Indexed {file_path}: {result['chunks']} chunks")
                    except Exception as e:
                        logger.error(f"Failed to index {file_path}: {e}")
            
            # Get final count
            final_count = self.qdrant_client.count(
                collection_name=self.collection_name
            ).count
            
            return {
                "status": "success",
                "indexed_files": indexed_files,
                "total_chunks": total_chunks,
                "previous_count": existing_count,
                "final_count": final_count,
                "new_documents": final_count - existing_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to index knowledge base: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def index_file(self, file_path: Path) -> Dict[str, Any]:
        """Index a single file into the knowledge base"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Classify content
            knowledge_type = NetworkKnowledgeSchema.classify_content(
                content, file_path.name
            )
            
            # Create document
            document = Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "knowledge_type": knowledge_type,
                    "indexed_at": datetime.utcnow().isoformat(),
                    "file_size": file_path.stat().st_size
                }
            )
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([document])
            
            # Add chunks to vector store
            if chunks:
                self.vector_store.add_documents(chunks)
            
            return {
                "status": "success",
                "chunks": len(chunks),
                "knowledge_type": knowledge_type
            }
            
        except Exception as e:
            logger.error(f"Failed to index file {file_path}: {e}")
            raise
    
    async def query_knowledge(
        self, 
        query: str, 
        knowledge_type: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information"""
        try:
            # Build filter if knowledge_type is specified
            filter_dict = None
            if knowledge_type:
                filter_dict = {
                    "must": [
                        {"key": "metadata.knowledge_type", "match": {"value": knowledge_type}}
                    ]
                }
            
            # Search vector store
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter_dict
            )
            
            # Filter by similarity threshold
            filtered_results = []
            for doc, score in results:
                if score >= similarity_threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": score
                    })
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            return []
    
    async def generate_response(
        self, 
        query: str, 
        context: Optional[List[Dict[str, Any]]] = None,
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response using RAG"""
        try:
            # Retrieve relevant knowledge
            knowledge_results = await self.query_knowledge(
                query=query,
                knowledge_type=knowledge_type,
                top_k=5
            )
            
            # Build context from knowledge results
            knowledge_context = ""
            if knowledge_results:
                knowledge_context = "\n\n".join([
                    f"[{result['metadata']['knowledge_type'].upper()}] {result['content']}"
                    for result in knowledge_results
                ])
            
            # Build full context
            full_context = ""
            if context:
                full_context += "Current Context:\n" + "\n".join([
                    f"- {ctx.get('type', 'unknown')}: {ctx.get('content', '')}"
                    for ctx in context
                ]) + "\n\n"
            
            if knowledge_context:
                full_context += "Relevant Knowledge:\n" + knowledge_context + "\n\n"
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""You are a senior Network Operations Center (NOC) engineer with expertise in network infrastructure, security, and troubleshooting.

CONTEXT:
{context}

QUESTION:
{question}

Based on the provided context and your expertise, provide a comprehensive NOC Action Plan. Include:

1. **Immediate Assessment**: What's the current situation and severity?
2. **Root Cause Analysis**: What are the likely causes?
3. **Step-by-Step Resolution**: Detailed steps to fix the issue
4. **Verification Steps**: How to confirm the issue is resolved
5. **Prevention Measures**: How to prevent similar issues
6. **Escalation Criteria**: When to escalate to senior engineers

Format your response as a structured NOC Action Plan with clear sections and actionable steps.

NOC ACTION PLAN:"""
            )
            
            # Generate response
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(),
                chain_type_kwargs={"prompt": prompt_template}
            )
            
            response = chain.run(query)
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "knowledge_results": knowledge_results,
                "context_used": bool(full_context),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def add_knowledge(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add new knowledge to the vector store"""
        try:
            # Auto-classify if not provided
            if not knowledge_type:
                knowledge_type = NetworkKnowledgeSchema.classify_content(
                    content, metadata.get("filename", "")
                )
            
            # Create document
            document = Document(
                page_content=content,
                metadata={
                    **metadata,
                    "knowledge_type": knowledge_type,
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            
            # Split and add to vector store
            chunks = self.text_splitter.split_documents([document])
            self.vector_store.add_documents(chunks)
            
            return {
                "status": "success",
                "chunks": len(chunks),
                "knowledge_type": knowledge_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            # Get total count
            total_count = self.qdrant_client.count(
                collection_name=self.collection_name
            ).count
            
            # Get knowledge type distribution
            # This would require a more complex query in production
            knowledge_types = list(NetworkKnowledgeSchema.KNOWLEDGE_TYPES.keys())
            
            return {
                "total_documents": total_count,
                "knowledge_types": knowledge_types,
                "collection_name": self.collection_name,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def search_by_metadata(
        self, 
        metadata_filter: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents by metadata"""
        try:
            # Build filter
            filter_dict = {
                "must": [
                    {"key": key, "match": {"value": value}}
                    for key, value in metadata_filter.items()
                ]
            }
            
            # Search with filter
            results = self.vector_store.similarity_search(
                query="",  # Empty query to get all matching documents
                k=limit,
                filter=filter_dict
            )
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to search by metadata: {e}")
            return []


# Global instance
knowledge_manager = KnowledgeManager()
