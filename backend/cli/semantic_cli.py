#!/usr/bin/env python3
"""
Semantic Search CLI Tool
Command line interface for managing semantic search functionality
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from services.embedding_service import embedding_service
from agents.agent_semantic import semantic_agent
from tasks.embedding_tasks import EmbeddingTaskManager
from database.database import SessionLocal
from database.models import Idea, User

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticCLI:
    """CLI interface for semantic search management"""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.semantic_agent = semantic_agent
        self.task_manager = EmbeddingTaskManager()
    
    async def generate_embeddings(self, batch_size: int = 50, force: bool = False):
        """Generate embeddings for ideas that don't have them"""
        print(f"🧠 Generating embeddings (batch size: {batch_size})")
        
        try:
            if force:
                # Clear existing embeddings first
                await self.clear_embeddings()
            
            result = await self.semantic_agent.batch_update_embeddings(batch_size)
            
            if result.get('success'):
                print(f"✅ Successfully updated {result['updated_count']} embeddings")
            else:
                print(f"❌ Failed to update embeddings: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
    
    async def clear_embeddings(self):
        """Clear all embeddings from the database"""
        print("🗑️  Clearing all embeddings...")
        
        try:
            db = SessionLocal()
            try:
                # Clear all embeddings
                ideas = db.query(Idea).filter(Idea.content_embedding.isnot(None)).all()
                
                for idea in ideas:
                    idea.content_embedding = None
                    idea.embedding_model = None
                    idea.embedding_updated_at = None
                
                db.commit()
                print(f"✅ Cleared embeddings for {len(ideas)} ideas")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error clearing embeddings: {e}")
    
    async def search_ideas(self, query: str, user_id: str, limit: int = 10, threshold: float = 0.5):
        """Search for ideas using semantic similarity"""
        print(f"🔍 Searching for: '{query}'")
        
        try:
            result = await self.semantic_agent.search_similar_ideas(
                query=query,
                user_id=user_id,
                limit=limit,
                threshold=threshold
            )
            
            if result.get('success'):
                results = result['results']
                print(f"📊 Found {len(results)} similar ideas:")
                
                for i, idea in enumerate(results, 1):
                    similarity = idea['similarity_score'] * 100
                    content = idea['content_processed'] or idea['content_transcribed'] or idea['content_raw']
                    print(f"  {i}. [{similarity:.1f}%] {content[:80]}...")
                    print(f"     Category: {idea['category']}, Created: {idea['created_at']}")
                    print()
            else:
                print(f"❌ Search failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    async def find_related(self, idea_id: str, limit: int = 5, threshold: float = 0.6):
        """Find ideas related to a specific idea"""
        print(f"🔗 Finding ideas related to: {idea_id}")
        
        try:
            result = await self.semantic_agent.find_related_ideas(
                idea_id=idea_id,
                limit=limit,
                threshold=threshold
            )
            
            if result.get('success'):
                related_ideas = result['related_ideas']
                print(f"📊 Found {len(related_ideas)} related ideas:")
                
                for i, idea in enumerate(related_ideas, 1):
                    similarity = idea['similarity_score'] * 100
                    content = idea['content_processed'] or idea['content_transcribed'] or idea['content_raw']
                    print(f"  {i}. [{similarity:.1f}%] {content[:80]}...")
                    print(f"     Category: {idea['category']}, Created: {idea['created_at']}")
                    print()
            else:
                print(f"❌ Failed to find related ideas: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error finding related ideas: {e}")
    
    async def get_stats(self):
        """Get embedding statistics"""
        print("📊 Embedding Statistics:")
        
        try:
            result = await self.semantic_agent.get_embedding_stats()
            
            if result.get('success'):
                stats = result['stats']
                
                print(f"  Total Ideas: {stats['total_ideas']:,}")
                print(f"  Ideas with Embeddings: {stats['ideas_with_embeddings']:,}")
                print(f"  Coverage: {stats['coverage_percentage']:.1f}%")
                print(f"  Current Model: {stats['current_model']}")
                print(f"  Embedding Dimension: {stats['embedding_dimension']}")
                
                if stats['model_stats']:
                    print("  Model Usage:")
                    for model, count in stats['model_stats'].items():
                        print(f"    {model}: {count:,} ideas")
                
            else:
                print(f"❌ Failed to get stats: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
    
    async def health_check(self):
        """Check health of semantic search system"""
        print("🏥 Semantic Search Health Check:")
        
        try:
            health = await self.task_manager.get_embedding_health()
            
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'error': '💥'
            }
            
            print(f"  Status: {status_emoji.get(health['status'], '❓')} {health['status']}")
            print(f"  Total Ideas: {health.get('total_ideas', 0):,}")
            print(f"  Ideas with Embeddings: {health.get('ideas_with_embeddings', 0):,}")
            print(f"  Coverage: {health.get('coverage_percentage', 0):.1f}%")
            print(f"  Pending Ideas: {health.get('pending_ideas', 0):,}")
            print(f"  Recent Updates (24h): {health.get('recent_updates_24h', 0):,}")
            print(f"  Task Manager Running: {health.get('task_manager_running', False)}")
            
        except Exception as e:
            print(f"❌ Health check error: {e}")
    
    async def test_similarity(self, text1: str, text2: str):
        """Test similarity between two texts"""
        print(f"🧪 Testing similarity between:")
        print(f"  Text 1: {text1}")
        print(f"  Text 2: {text2}")
        
        try:
            # Generate embeddings
            emb1 = await self.embedding_service.generate_embedding(text1)
            emb2 = await self.embedding_service.generate_embedding(text2)
            
            # Calculate similarity
            similarity = self.embedding_service.calculate_similarity(emb1, emb2)
            
            print(f"  Similarity: {similarity * 100:.1f}%")
            
            if similarity > 0.8:
                print("  💚 Very similar")
            elif similarity > 0.6:
                print("  💛 Somewhat similar")
            elif similarity > 0.4:
                print("  🧡 Slightly similar")
            else:
                print("  💙 Not very similar")
                
        except Exception as e:
            print(f"❌ Similarity test error: {e}")
    
    async def benchmark_search(self, num_queries: int = 10):
        """Benchmark search performance"""
        print(f"⚡ Benchmarking search performance ({num_queries} queries)")
        
        try:
            import time
            
            # Get some sample ideas for queries
            db = SessionLocal()
            try:
                ideas = db.query(Idea).filter(
                    Idea.content_embedding.isnot(None)
                ).limit(num_queries).all()
                
                if not ideas:
                    print("❌ No ideas with embeddings found for benchmarking")
                    return
                
                total_time = 0
                successful_searches = 0
                
                for idea in ideas:
                    content = idea.content_processed or idea.content_transcribed or idea.content_raw
                    if not content:
                        continue
                    
                    start_time = time.time()
                    
                    result = await self.semantic_agent.search_similar_ideas(
                        query=content[:50],  # Use first 50 chars as query
                        user_id=idea.user_id,
                        limit=5,
                        threshold=0.5
                    )
                    
                    end_time = time.time()
                    query_time = end_time - start_time
                    total_time += query_time
                    
                    if result.get('success'):
                        successful_searches += 1
                        print(f"  Query {successful_searches}: {query_time:.3f}s - {len(result['results'])} results")
                    else:
                        print(f"  Query failed: {result.get('error')}")
                
                if successful_searches > 0:
                    avg_time = total_time / successful_searches
                    print(f"  Average search time: {avg_time:.3f}s")
                    print(f"  Success rate: {successful_searches}/{num_queries} ({successful_searches/num_queries*100:.1f}%)")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Benchmark error: {e}")
    
    def list_users(self):
        """List available users"""
        print("👥 Available Users:")
        
        try:
            db = SessionLocal()
            try:
                users = db.query(User).all()
                
                for user in users:
                    idea_count = db.query(Idea).filter(Idea.user_id == user.id).count()
                    embedding_count = db.query(Idea).filter(
                        Idea.user_id == user.id,
                        Idea.content_embedding.isnot(None)
                    ).count()
                    
                    print(f"  {user.id}: {user.username} ({user.email})")
                    print(f"    Ideas: {idea_count}, Embeddings: {embedding_count}")
                    print()
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error listing users: {e}")

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Semantic Search CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate embeddings
    gen_parser = subparsers.add_parser('generate', help='Generate embeddings')
    gen_parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    gen_parser.add_argument('--force', action='store_true', help='Force regenerate all embeddings')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search for similar ideas')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--user-id', required=True, help='User ID to search within')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum results')
    search_parser.add_argument('--threshold', type=float, default=0.5, help='Similarity threshold')
    
    # Related
    related_parser = subparsers.add_parser('related', help='Find related ideas')
    related_parser.add_argument('idea_id', help='Idea ID to find related ideas for')
    related_parser.add_argument('--limit', type=int, default=5, help='Maximum results')
    related_parser.add_argument('--threshold', type=float, default=0.6, help='Similarity threshold')
    
    # Stats
    subparsers.add_parser('stats', help='Show embedding statistics')
    
    # Health
    subparsers.add_parser('health', help='Check system health')
    
    # Test similarity
    test_parser = subparsers.add_parser('test', help='Test similarity between two texts')
    test_parser.add_argument('text1', help='First text')
    test_parser.add_argument('text2', help='Second text')
    
    # Benchmark
    bench_parser = subparsers.add_parser('benchmark', help='Benchmark search performance')
    bench_parser.add_argument('--queries', type=int, default=10, help='Number of queries to test')
    
    # Clear embeddings
    subparsers.add_parser('clear', help='Clear all embeddings')
    
    # List users
    subparsers.add_parser('users', help='List available users')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = SemanticCLI()
    
    if args.command == 'generate':
        await cli.generate_embeddings(args.batch_size, args.force)
    elif args.command == 'search':
        await cli.search_ideas(args.query, args.user_id, args.limit, args.threshold)
    elif args.command == 'related':
        await cli.find_related(args.idea_id, args.limit, args.threshold)
    elif args.command == 'stats':
        await cli.get_stats()
    elif args.command == 'health':
        await cli.health_check()
    elif args.command == 'test':
        await cli.test_similarity(args.text1, args.text2)
    elif args.command == 'benchmark':
        await cli.benchmark_search(args.queries)
    elif args.command == 'clear':
        await cli.clear_embeddings()
    elif args.command == 'users':
        cli.list_users()

if __name__ == "__main__":
    asyncio.run(main())