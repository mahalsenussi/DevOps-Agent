"""
Memory Store - ChromaDB-based persistent memory for the agent
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

from ..config import get_config


class MemoryStore:
    """Persistent memory store using ChromaDB"""
    
    def __init__(self, persist_dir: Optional[str] = None):
        config = get_config()
        self.persist_dir = persist_dir or config.memory_persist_dir
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection for conversations
        self.conversation_collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Agent conversation history"}
        )
        
        # Create or get collection for knowledge
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge",
            metadata={"description": "Agent knowledge base"}
        )
    
    def add_conversation(
        self, 
        user_input: str, 
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a conversation to memory"""
        timestamp = datetime.now().isoformat()
        
        # Generate unique ID
        doc_id = f"conv_{timestamp}"
        
        # Combine user input and response
        content = f"User: {user_input}\nAgent: {agent_response}"
        
        # Add metadata
        meta = metadata or {}
        meta.update({
            "timestamp": timestamp,
            "type": "conversation"
        })
        
        self.conversation_collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta]
        )
    
    def add_knowledge(
        self,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add knowledge to the knowledge base"""
        timestamp = datetime.now().isoformat()
        doc_id = f"knowledge_{timestamp}"
        
        meta = metadata or {}
        meta.update({
            "timestamp": timestamp,
            "category": category
        })
        
        self.knowledge_collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta]
        )
    
    def search_conversations(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search past conversations"""
        results = self.conversation_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return self._format_results(results)
    
    def search_knowledge(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        results = self.knowledge_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return self._format_results(results)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        # Get all documents and sort by timestamp
        results = self.conversation_collection.get()
        
        docs = []
        for i, doc in enumerate(results.get("documents", [])):
            meta = results.get("metadatas", [{}])[i]
            docs.append({
                "content": doc,
                "metadata": meta
            })
        
        # Sort by timestamp and return recent
        docs.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        return docs[:limit]
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB results"""
        formatted = []
        
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        for i, doc in enumerate(documents):
            formatted.append({
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })
        
        return formatted
    
    def clear_conversations(self) -> None:
        """Clear all conversation history"""
        self.conversation_collection.delete(where={"type": "conversation"})
    
    def clear_knowledge(self) -> None:
        """Clear all knowledge"""
        self.knowledge_collection.delete(where={})


# Global memory instance
_memory_store: Optional[MemoryStore] = None


def get_memory() -> MemoryStore:
    """Get or create global memory store instance"""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store