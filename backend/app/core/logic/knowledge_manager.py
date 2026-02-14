"""
NOCbRAIN Knowledge Manager
RAG (Retrieval-Augmented Generation) implementation with strict multi-tenancy
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging
import uuid

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
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


class TenantAwareKnowledgeManager:
    """Multi-tenant knowledge management service with strict isolation"""
    
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
        
        # Collection names
        self.global_collection = "nocbrain_global_knowledge"
        self.private_collection_prefix = "nocbrain_tenant_"
        
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
        
        logger.info("Multi-tenant Knowledge Manager initialized")
    
    def _get_collection_name(self, tenant_id: str) -> str:
        """Get collection name for tenant"""
        if tenant_id == "global":
            return self.global_collection
        return f"{self.private_collection_prefix}{tenant_id}"
    
    def _create_tenant_filter(self, tenant_id: str) -> Optional[Filter]:
        """Create tenant filter for vector search"""
        if tenant_id == "global":
            # Global tenant can search all collections
            return None
        
        # Private tenant can only search their own collection
        return Filter(
            must=[
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id)
                )
            ]
        )
    
    async def initialize_collection(self, tenant_id: str = "global"):
        """Initialize Qdrant collection for tenant"""
        try:
            collection_name = self._get_collection_name(tenant_id)
            
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(
                collection.name == collection_name 
                for collection in collections
            )
            
            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection {collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection for tenant {tenant_id}: {e}")
            raise
    
    async def index_knowledge_base(self, tenant_id: str = "global", force_reindex: bool = False) -> Dict[str, Any]:
        """Index knowledge base for specific tenant"""
        try:
            await self.initialize_collection(tenant_id)
            
            collection_name = self._get_collection_name(tenant_id)
            
            # Get existing documents count
            existing_count = self.qdrant_client.count(
                collection_name=collection_name
            ).count
            
            if force_reindex:
                logger.info(f"Force reindexing tenant {tenant_id} - clearing existing collection")
                self.qdrant_client.delete_collection(collection_name)
                await self.initialize_collection(tenant_id)
                existing_count = 0
            
            # Process knowledge base files
            indexed_files = 0
            total_chunks = 0
            
            for file_path in self.knowledge_base_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.log', '.conf', '.yaml', '.yml', '.json']:
                    try:
                        result = await self.index_file(file_path, tenant_id)
                        indexed_files += 1
                        total_chunks += result['chunks']
                        logger.info(f"Indexed {file_path} for tenant {tenant_id}: {result['chunks']} chunks")
                    except Exception as e:
                        logger.error(f"Failed to index {file_path} for tenant {tenant_id}: {e}")
            
            # Get final count
            final_count = self.qdrant_client.count(
                collection_name=collection_name
            ).count
            
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "indexed_files": indexed_files,
                "total_chunks": total_chunks,
                "previous_count": existing_count,
                "final_count": final_count,
                "new_documents": final_count - existing_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to index knowledge base for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "tenant_id": tenant_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def index_file(self, file_path: Path, tenant_id: str) -> Dict[str, Any]:
        """Index a single file into tenant's knowledge base"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Classify content
            knowledge_type = NetworkKnowledgeSchema.classify_content(
                content, file_path.name
            )
            
            # Create document with tenant isolation
            document = Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "knowledge_type": knowledge_type,
                    "tenant_id": tenant_id,
                    "indexed_at": datetime.utcnow().isoformat(),
                    "file_size": file_path.stat().st_size,
                    "is_global": tenant_id == "global"
                }
            )
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([document])
            
            # Add tenant_id to all chunk metadata
            for chunk in chunks:
                chunk.metadata["tenant_id"] = tenant_id
                chunk.metadata["is_global"] = tenant_id == "global"
            
            # Get tenant-specific vector store
            vector_store = self._get_tenant_vector_store(tenant_id)
            
            # Add chunks to vector store
            if chunks:
                vector_store.add_documents(chunks)
            
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "chunks": len(chunks),
                "knowledge_type": knowledge_type
            }
            
        except Exception as e:
            logger.error(f"Failed to index file {file_path} for tenant {tenant_id}: {e}")
            raise
    
    def _get_tenant_vector_store(self, tenant_id: str) -> Qdrant:
        """Get tenant-specific vector store"""
        collection_name = self._get_collection_name(tenant_id)
        
        return Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=self.embeddings
        )
    
    async def query_knowledge(
        self, 
        query: str, 
        tenant_id: str,
        knowledge_type: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        include_global: bool = True
    ) -> List[Dict[str, Any]]:
        """Query knowledge base with strict tenant isolation"""
        try:
            # Build filter for tenant isolation
            tenant_filter = self._create_tenant_filter(tenant_id)
            
            # Search in tenant's private collection
            private_vector_store = self._get_tenant_vector_store(tenant_id)
            
            # Add knowledge type filter if specified
            if knowledge_type:
                if tenant_filter:
                    tenant_filter.must.append(
                        FieldCondition(
                            key="metadata.knowledge_type",
                            match=MatchValue(value=knowledge_type)
                        )
                    )
                else:
                    tenant_filter = Filter(
                        must=[
                            FieldCondition(
                                key="metadata.knowledge_type",
                                match=MatchValue(value=knowledge_type)
                            ),
                            FieldCondition(
                                key="tenant_id",
                                match=MatchValue(value=tenant_id)
                            )
                        ]
                    )
            
            # Search tenant's private collection
            private_results = []
            try:
                private_results = private_vector_store.similarity_search_with_score(
                    query=query,
                    k=top_k,
                    filter=tenant_filter
                )
            except Exception as e:
                logger.error(f"Error searching private collection for tenant {tenant_id}: {e}")
            
            # Include global knowledge if requested and tenant is not global
            global_results = []
            if include_global and tenant_id != "global":
                try:
                    global_vector_store = self._get_tenant_vector_store("global")
                    global_results = global_vector_store.similarity_search_with_score(
                        query=query,
                        k=max(1, top_k // 2),  # Get half from global
                        filter=Filter(
                            must=[
                                FieldCondition(
                                    key="metadata.is_global",
                                    match=MatchValue(value=True)
                                )
                            ]
                        )
                    )
                except Exception as e:
                    logger.error(f"Error searching global collection: {e}")
            
            # Combine and filter results
            all_results = private_results + global_results
            filtered_results = []
            
            for doc, score in all_results:
                if score >= similarity_threshold:
                    # Ensure tenant isolation
                    metadata = doc.metadata
                    
                    # Allow if it's tenant's own document or global
                    if (metadata.get("tenant_id") == tenant_id or 
                        metadata.get("is_global", False)):
                        
                        filtered_results.append({
                            "content": doc.page_content,
                            "metadata": metadata,
                            "similarity_score": score,
                            "source": "private" if metadata.get("tenant_id") == tenant_id else "global"
                        })
            
            # Sort by similarity score and limit results
            filtered_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to query knowledge base for tenant {tenant_id}: {e}")
            return []
    
    async def generate_response(
        self, 
        query: str, 
        tenant_id: str,
        context: Optional[List[Dict[str, Any]]] = None,
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response using RAG with tenant isolation"""
        try:
            # Retrieve relevant knowledge with tenant isolation
            knowledge_results = await self.query_knowledge(
                query=query,
                tenant_id=tenant_id,
                knowledge_type=knowledge_type,
                top_k=5,
                include_global=True
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
            
            # Get tenant-specific vector store for chain
            vector_store = self._get_tenant_vector_store(tenant_id)
            
            # Generate response
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(),
                chain_type_kwargs={"prompt": prompt_template}
            )
            
            response = chain.run(query)
            
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "query": query,
                "response": response,
                "knowledge_results": knowledge_results,
                "context_used": bool(full_context),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "tenant_id": tenant_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def add_knowledge(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        tenant_id: str,
        knowledge_type: Optional[str] = None,
        is_global: bool = False
    ) -> Dict[str, Any]:
        """Add knowledge with tenant isolation"""
        try:
            # Auto-classify if not provided
            if not knowledge_type:
                knowledge_type = NetworkKnowledgeSchema.classify_content(
                    content, metadata.get("filename", "")
                )
            
            # Create document with tenant isolation
            document = Document(
                page_content=content,
                metadata={
                    **metadata,
                    "knowledge_type": knowledge_type,
                    "tenant_id": tenant_id,
                    "is_global": is_global,
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            
            # Split and add to tenant's vector store
            chunks = self.text_splitter.split_documents([document])
            
            # Add tenant_id to all chunk metadata
            for chunk in chunks:
                chunk.metadata["tenant_id"] = tenant_id
                chunk.metadata["is_global"] = is_global
            
            # Get tenant-specific vector store
            vector_store = self._get_tenant_vector_store(tenant_id)
            
            # Add chunks to vector store
            vector_store.add_documents(chunks)
            
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "chunks": len(chunks),
                "knowledge_type": knowledge_type,
                "is_global": is_global,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add knowledge for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "tenant_id": tenant_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for specific tenant"""
        try:
            collection_name = self._get_collection_name(tenant_id)
            
            # Get total count
            total_count = self.qdrant_client.count(
                collection_name=collection_name
            ).count
            
            # Get knowledge type distribution
            knowledge_types = list(NetworkKnowledgeSchema.KNOWLEDGE_TYPES.keys())
            
            return {
                "tenant_id": tenant_id,
                "total_documents": total_count,
                "knowledge_types": knowledge_types,
                "collection_name": collection_name,
                "is_global": tenant_id == "global",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "tenant_id": tenant_id,
                "error": str(e)
            }
    
    async def search_by_metadata(
        self, 
        tenant_id: str,
        metadata_filter: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents by metadata with tenant isolation"""
        try:
            # Build filter with tenant isolation
            filter_conditions = [
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id)
                )
            ]
            
            # Add metadata filters
            for key, value in metadata_filter.items():
                filter_conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            
            filter_dict = Filter(must=filter_conditions)
            
            # Search with filter
            vector_store = self._get_tenant_vector_store(tenant_id)
            results = vector_store.similarity_search(
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
            logger.error(f"Failed to search by metadata for tenant {tenant_id}: {e}")
            return []
    
    async def delete_tenant_data(self, tenant_id: str) -> Dict[str, Any]:
        """Delete all data for specific tenant"""
        try:
            if tenant_id == "global":
                raise ValueError("Cannot delete global tenant data")
            
            collection_name = self._get_collection_name(tenant_id)
            
            # Delete collection
            self.qdrant_client.delete_collection(collection_name)
            
            logger.info(f"Deleted collection for tenant {tenant_id}")
            
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "collection_name": collection_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete tenant data for {tenant_id}: {e}")
            return {
                "status": "error",
                "tenant_id": tenant_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance
knowledge_manager = TenantAwareKnowledgeManager()
