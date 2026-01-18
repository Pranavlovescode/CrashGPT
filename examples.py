#!/usr/bin/env python3
"""
Practical examples of using CrashGPT RAG server.
Shows different query patterns and how to interpret results.
"""

from client import CrashGPTClient
import json

def example_1_basic_upload_and_query():
    """Example 1: Basic upload and query workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Upload and Query")
    print("="*70)
    
    client = CrashGPTClient()
    
    # Upload a log file
    print("\nUploading mysql_crash_log_detailed.txt...")
    upload_result = client.upload_log(
        'mysql_crash_log_detailed.txt',
        collection_name='example1_mysql'
    )
    print(f"✓ Uploaded: {upload_result['message']}")
    
    # Ask a simple question
    query = "Why did MySQL fail?"
    print(f"\nQuery: {query}")
    result = client.query(query, collection_name='example1_mysql')
    
    print(f"\nAnswer:\n{result['answer']}\n")
    print(f"Retrieved {len(result['sources'])} relevant log segments")


def example_2_multiple_queries():
    """Example 2: Multiple related queries on same collection"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multiple Related Queries")
    print("="*70)
    
    client = CrashGPTClient()
    
    # Make sure collection exists
    print("\nUploading logs for multi-query analysis...")
    client.upload_log('mysql_crash_log_detailed.txt', 'example2_mysql')
    
    queries = [
        "What is the root cause of the failure?",
        "What error codes appear in the logs?",
        "What should I do to fix this?",
        "How can I prevent this error?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        result = client.query(query, collection_name='example2_mysql', limit=6)
        
        # Extract just the first part of answer for brevity
        answer_lines = result['answer'].split('\n')[:5]
        print('\n'.join(answer_lines))
        print(f"[Based on {len(result['sources'])} relevant log segments]")


def example_3_adjusting_retrieval_limit():
    """Example 3: Compare different retrieval limits (limit parameter)"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Impact of Retrieval Limit")
    print("="*70)
    
    client = CrashGPTClient()
    client.upload_log('mysql_crash_log_detailed.txt', 'example3_mysql')
    
    query = "What caused the database corruption?"
    
    for limit in [2, 4, 8]:
        print(f"\n--- Query with limit={limit} ---")
        result = client.query(query, collection_name='example3_mysql', limit=limit)
        
        print(f"Retrieved {len(result['sources'])} chunks")
        print(f"Source scores: {[f\"{s['score']:.3f}\" for s in result['sources']]}")
        
        # Show relevance
        avg_score = sum(s['score'] for s in result['sources']) / len(result['sources'])
        print(f"Average relevance score: {avg_score:.3f}")
        
        # Show answer length
        answer_length = len(result['answer'])
        print(f"Answer length: {answer_length} characters")


def example_4_analyzing_sources():
    """Example 4: Deep dive into source document analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Analyzing Source Documents")
    print("="*70)
    
    client = CrashGPTClient()
    client.upload_log('mysql_crash_log_detailed.txt', 'example4_mysql')
    
    query = "What InnoDB errors occurred?"
    print(f"\nQuery: {query}")
    
    result = client.query(query, collection_name='example4_mysql', limit=6)
    
    print(f"\n{len(result['sources'])} relevant sources found:")
    print("-" * 70)
    
    for i, source in enumerate(result['sources'], 1):
        # Unpack source details
        score = source['score']
        content = source['content']
        source_file = source['source']
        
        # Determine relevance level
        if score > 0.8:
            relevance = "🟢 Highly Relevant"
        elif score > 0.6:
            relevance = "🟡 Relevant"
        else:
            relevance = "🔴 Loosely Related"
        
        print(f"\n[Source {i}] {relevance} (Score: {score:.4f})")
        print(f"From: {source_file}")
        print(f"Content: {content[:150]}...")


def example_5_error_handling():
    """Example 5: Error handling and edge cases"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling")
    print("="*70)
    
    client = CrashGPTClient()
    
    # Try to query non-existent collection
    print("\n1. Querying non-existent collection:")
    try:
        result = client.query("What failed?", collection_name='non_existent')
        print("Query succeeded (unexpected)")
    except Exception as e:
        print(f"✓ Caught error: {str(e)[:80]}...")
    
    # Upload then query
    print("\n2. Normal upload and query:")
    client.upload_log('mysql_crash_log_detailed.txt', 'example5_mysql')
    try:
        result = client.query("What failed?", collection_name='example5_mysql')
        print(f"✓ Query succeeded with {len(result['sources'])} sources")
    except Exception as e:
        print(f"Error: {e}")
    
    # List collections
    print("\n3. List available collections:")
    try:
        collections = client.list_collections()
        print(f"✓ Found {len(collections)} collections:")
        for col in collections:
            print(f"  - {col['name']}: {col['vectors_count']} vectors")
    except Exception as e:
        print(f"Error: {e}")


def example_6_comparing_log_quality():
    """Example 6: Compare answers from different log qualities"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Log Quality Impact on Answer Quality")
    print("="*70)
    
    client = CrashGPTClient()
    
    query = "What is the root cause of the failure?"
    
    # Upload both log files
    print("\nUploading simple log...")
    client.upload_log('mysql_crash_log.txt', 'example6_simple')
    
    print("Uploading detailed log...")
    client.upload_log('mysql_crash_log_detailed.txt', 'example6_detailed')
    
    # Query both
    print(f"\nQuerying: {query}")
    print("\n" + "-"*70)
    print("SIMPLE LOG ANSWER:")
    print("-"*70)
    result_simple = client.query(query, collection_name='example6_simple', limit=6)
    print(result_simple['answer'])
    
    print("\n" + "-"*70)
    print("DETAILED LOG ANSWER:")
    print("-"*70)
    result_detailed = client.query(query, collection_name='example6_detailed', limit=6)
    print(result_detailed['answer'])
    
    print("\n" + "-"*70)
    print("COMPARISON:")
    print("-"*70)
    print(f"Simple log uses avg score: {sum(s['score'] for s in result_simple['sources']) / len(result_simple['sources']):.3f}")
    print(f"Detailed log uses avg score: {sum(s['score'] for s in result_detailed['sources']) / len(result_detailed['sources']):.3f}")
    print(f"Simple log answer length: {len(result_simple['answer'])} chars")
    print(f"Detailed log answer length: {len(result_detailed['answer'])} chars")


def example_7_production_pattern():
    """Example 7: Production-like usage pattern"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Production Pattern - Multiple Log Types")
    print("="*70)
    
    client = CrashGPTClient()
    
    # In production, you'd have different log files for different services
    log_files = [
        ('mysql_crash_log_detailed.txt', 'production_mysql_logs'),
    ]
    
    print("\nSetting up log collections...")
    for file, collection in log_files:
        try:
            result = client.upload_log(file, collection)
            print(f"✓ {collection}: {result['message']}")
        except FileNotFoundError:
            print(f"✗ {collection}: File not found")
    
    # Production queries
    queries = [
        ("production_mysql_logs", "Are there any error states in the logs?"),
        ("production_mysql_logs", "What recovery attempts were made?"),
    ]
    
    print("\nRunning production queries...")
    for collection, query in queries:
        print(f"\n[{collection}] {query}")
        try:
            result = client.query(query, collection_name=collection, limit=5)
            # In production, you'd store this result
            print(f"✓ Got answer based on {len(result['sources'])} sources")
        except Exception as e:
            print(f"✗ Error: {str(e)[:60]}...")


def main():
    """Run all examples"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "CrashGPT RAG Examples - Guide".center(38) + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    
    examples = [
        ("Basic upload and query", example_1_basic_upload_and_query),
        ("Multiple related queries", example_2_multiple_queries),
        ("Impact of retrieval limit", example_3_adjusting_retrieval_limit),
        ("Analyzing source documents", example_4_analyzing_sources),
        ("Error handling", example_5_error_handling),
        ("Log quality comparison", example_6_comparing_log_quality),
        ("Production pattern", example_7_production_pattern),
    ]
    
    while True:
        print("\n" + "="*70)
        print("Available Examples:")
        print("="*70)
        for i, (name, _) in enumerate(examples, 1):
            print(f"{i}. {name}")
        print("0. Exit")
        
        choice = input("\nSelect example (0-7): ").strip()
        
        if choice == "0":
            print("\nGoodbye!")
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                print(f"\nRunning: {name}")
                func()
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Make sure the CrashGPT server is running (python server.py)")


if __name__ == "__main__":
    main()
