"""
Policy management service with semantic search using ChromaDB.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from loguru import logger

from ..config import get_settings
from ..models.policy import Policy, PolicyCategory, PolicySearchResult, PolicyCreate, PolicyUpdate
from .cache_service import cache_service


class PolicyService:
    """Policy management service with semantic search capabilities."""
    
    def __init__(self):
        """Initialize policy service with ChromaDB and embeddings."""
        self.settings = get_settings()
        self.chroma_client = None
        self.embedding_model = None
        self.collection = None
        self._initialize_chroma()
        self._initialize_embeddings()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for policies
            self.collection = self.chroma_client.get_or_create_collection(
                name="company_policies",
                metadata={"description": "Company policies and FAQs for email responses"}
            )
            
            logger.info("ChromaDB policy collection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _initialize_embeddings(self):
        """Initialize sentence transformer model for embeddings."""
        try:
            self.embedding_model = SentenceTransformer(self.settings.embedding_model)
            logger.info(f"Embedding model initialized: {self.settings.embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text to use as cache key."""
        return hashlib.md5(text.encode()).hexdigest()
    
    async def add_policy(self, policy_data: PolicyCreate) -> Policy:
        """Add new policy to the system."""
        try:
            # Generate policy ID
            policy_id = str(uuid.uuid4())
            
            # Create policy object
            policy = Policy(
                id=policy_id,
                title=policy_data.title,
                content=policy_data.content,
                category=policy_data.category,
                tags=policy_data.tags,
                author=policy_data.author,
                version=policy_data.version,
                metadata=policy_data.metadata
            )
            
            # Generate embedding for policy content
            embedding = await self._get_cached_embedding(policy.content)
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[policy.content],
                metadatas=[{
                    'policy_id': policy_id,
                    'title': policy.title,
                    'category': policy.category.value,
                    'tags': ','.join(policy.tags),
                    'version': policy.version,
                    'author': policy.author,
                    'effective_date': policy.effective_date.isoformat(),
                    'is_active': str(policy.is_active)
                }],
                ids=[policy_id]
            )
            
            # Cache policy data
            await cache_service.set_policy(policy_id, policy.dict())
            
            # Save to file system
            await self._save_policy_to_file(policy)
            
            logger.info(f"Policy added successfully: {policy_id}")
            return policy
            
        except Exception as e:
            logger.error(f"Error adding policy: {e}")
            raise
    
    async def _get_cached_embedding(self, text: str) -> List[float]:
        """Get embedding from cache or generate new one."""
        text_hash = self._get_text_hash(text)
        
        # Try to get from cache first
        cached_embedding = await cache_service.get_embedding(text_hash)
        if cached_embedding:
            return cached_embedding
        
        # Generate new embedding
        embedding = self._generate_embedding(text)
        
        # Cache the embedding
        await cache_service.set_embedding(text_hash, embedding)
        
        return embedding
    
    async def _save_policy_to_file(self, policy: Policy):
        """Save policy to file system."""
        try:
            policy_file = self.settings.policies_dir / f"{policy.id}.json"
            
            with open(policy_file, 'w') as f:
                json.dump(policy.dict(), f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving policy to file: {e}")
    
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID."""
        try:
            # Try cache first
            cached_policy = await cache_service.get_policy(policy_id)
            if cached_policy:
                return Policy(**cached_policy)
            
            # Get from ChromaDB
            results = self.collection.get(ids=[policy_id])
            if not results['ids']:
                return None
            
            # Reconstruct policy from metadata
            metadata = results['metadatas'][0]
            policy = Policy(
                id=policy_id,
                title=metadata['title'],
                content=results['documents'][0],
                category=PolicyCategory(metadata['category']),
                tags=metadata['tags'].split(',') if metadata['tags'] else [],
                version=metadata['version'],
                author=metadata['author'],
                effective_date=datetime.fromisoformat(metadata['effective_date']),
                is_active=metadata['is_active'].lower() == 'true'
            )
            
            # Cache the policy
            await cache_service.set_policy(policy_id, policy.dict())
            
            return policy
            
        except Exception as e:
            logger.error(f"Error getting policy {policy_id}: {e}")
            return None
    
    async def search_policies(self, query: str, category: Optional[PolicyCategory] = None, 
                            limit: int = 5) -> List[PolicySearchResult]:
        """Search policies using semantic search."""
        try:
            # Generate query embedding
            query_embedding = await self._get_cached_embedding(query)
            
            # Prepare where clause for category filter
            where_clause = None
            if category:
                where_clause = {"category": category.value}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            search_results = []
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0], results['documents'][0], 
                results['metadatas'][0], results['distances'][0]
            )):
                # Convert distance to relevance score (1 - distance)
                relevance_score = 1.0 - distance
                
                # Create policy object
                policy = Policy(
                    id=doc_id,
                    title=metadata['title'],
                    content=document,
                    category=PolicyCategory(metadata['category']),
                    tags=metadata['tags'].split(',') if metadata['tags'] else [],
                    version=metadata['version'],
                    author=metadata['author'],
                    effective_date=datetime.fromisoformat(metadata['effective_date']),
                    is_active=metadata['is_active'].lower() == 'true'
                )
                
                # Create search result
                search_result = PolicySearchResult(
                    policy=policy,
                    relevance_score=relevance_score,
                    matched_terms=[query],  # Simplified for now
                    context=document[:200] + "..." if len(document) > 200 else document
                )
                
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} policies for query: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching policies: {e}")
            return []
    
    async def update_policy(self, policy_id: str, updates: PolicyUpdate) -> Optional[Policy]:
        """Update existing policy."""
        try:
            # Get current policy
            current_policy = await self.get_policy(policy_id)
            if not current_policy:
                return None
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(current_policy, field, value)
            
            # Update timestamps
            current_policy.last_updated = datetime.utcnow()
            
            # Update embedding if content changed
            if 'content' in update_data:
                new_embedding = await self._get_cached_embedding(current_policy.content)
                
                # Update in ChromaDB
                self.collection.update(
                    ids=[policy_id],
                    embeddings=[new_embedding],
                    documents=[current_policy.content],
                    metadatas=[{
                        'policy_id': policy_id,
                        'title': current_policy.title,
                        'category': current_policy.category.value,
                        'tags': ','.join(current_policy.tags),
                        'version': current_policy.version,
                        'author': current_policy.author,
                        'effective_date': current_policy.effective_date.isoformat(),
                        'is_active': str(current_policy.is_active)
                    }]
                )
            
            # Update cache
            await cache_service.set_policy(policy_id, current_policy.dict())
            
            # Update file
            await self._save_policy_to_file(current_policy)
            
            logger.info(f"Policy updated successfully: {policy_id}")
            return current_policy
            
        except Exception as e:
            logger.error(f"Error updating policy {policy_id}: {e}")
            return None
    
    async def delete_policy(self, policy_id: str) -> bool:
        """Delete policy from the system."""
        try:
            # Remove from ChromaDB
            self.collection.delete(ids=[policy_id])
            
            # Remove from cache
            await cache_service.invalidate_policy_cache(policy_id)
            
            # Remove file
            policy_file = self.settings.policies_dir / f"{policy_id}.json"
            if policy_file.exists():
                policy_file.unlink()
            
            logger.info(f"Policy deleted successfully: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting policy {policy_id}: {e}")
            return False
    
    async def get_policies_by_category(self, category: PolicyCategory) -> List[Policy]:
        """Get all policies in a specific category."""
        try:
            results = self.collection.get(
                where={"category": category.value}
            )
            
            policies = []
            for i, (doc_id, document, metadata) in enumerate(zip(
                results['ids'], results['documents'], results['metadatas']
            )):
                policy = Policy(
                    id=doc_id,
                    title=metadata['title'],
                    content=document,
                    category=PolicyCategory(metadata['category']),
                    tags=metadata['tags'].split(',') if metadata['tags'] else [],
                    version=metadata['version'],
                    author=metadata['author'],
                    effective_date=datetime.fromisoformat(metadata['effective_date']),
                    is_active=metadata['is_active'].lower() == 'true'
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            logger.error(f"Error getting policies by category {category}: {e}")
            return []
    
    async def get_all_policies(self) -> List[Policy]:
        """Get all policies in the system."""
        try:
            results = self.collection.get()
            
            policies = []
            for i, (doc_id, document, metadata) in enumerate(zip(
                results['ids'], results['documents'], results['metadatas']
            )):
                policy = Policy(
                    id=doc_id,
                    title=metadata['title'],
                    content=document,
                    category=PolicyCategory(metadata['category']),
                    tags=metadata['tags'].split(',') if metadata['tags'] else [],
                    version=metadata['version'],
                    author=metadata['author'],
                    effective_date=datetime.fromisoformat(metadata['effective_date']),
                    is_active=metadata['is_active'].lower() == 'true'
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            logger.error(f"Error getting all policies: {e}")
            return []
    
    async def get_policy_stats(self) -> Dict[str, Any]:
        """Get statistics about policies."""
        try:
            all_policies = await self.get_all_policies()
            
            stats = {
                'total_policies': len(all_policies),
                'active_policies': len([p for p in all_policies if p.is_active]),
                'categories': {},
                'recent_updates': []
            }
            
            # Count by category
            for policy in all_policies:
                category = policy.category.value
                if category not in stats['categories']:
                    stats['categories'][category] = 0
                stats['categories'][category] += 1
            
            # Recent updates (last 10)
            recent_policies = sorted(
                all_policies, 
                key=lambda p: p.last_updated, 
                reverse=True
            )[:10]
            
            stats['recent_updates'] = [
                {
                    'id': p.id,
                    'title': p.title,
                    'last_updated': p.last_updated.isoformat()
                }
                for p in recent_policies
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting policy stats: {e}")
            return {}


# Global policy service instance
policy_service = PolicyService() 