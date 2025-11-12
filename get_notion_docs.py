#!/usr/bin/env python3
"""
Script to fetch and display Notion document names.
"""
import os
import requests
import json

NOTION_API_SECRET = os.environ.get('notion_api_secret')
NOTION_API_VERSION = '2022-06-28'

def get_notion_documents():
    """Fetch all pages/documents from Notion."""
    headers = {
        'Authorization': f'Bearer {NOTION_API_SECRET}',
        'Notion-Version': NOTION_API_VERSION,
        'Content-Type': 'application/json'
    }
    
    # Search for all pages
    url = 'https://api.notion.com/v1/search'
    payload = {
        'filter': {
            'property': 'object',
            'value': 'page'
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        documents = []
        for result in data.get('results', []):
            # Extract title from page properties
            title = 'Untitled'
            if 'properties' in result:
                # Try to find title property (can be in different formats)
                for prop_name, prop_value in result['properties'].items():
                    if prop_value.get('type') == 'title' and prop_value.get('title'):
                        if prop_value['title']:
                            title = ''.join([text.get('plain_text', '') for text in prop_value['title']])
                            break
                    elif prop_name.lower() == 'title' or prop_name.lower() == 'name':
                        if isinstance(prop_value, dict) and 'title' in prop_value:
                            if prop_value['title']:
                                title = ''.join([text.get('plain_text', '') for text in prop_value['title']])
                                break
            
            # Fallback: try to get title from the page object itself
            if title == 'Untitled' and 'title' in result:
                if isinstance(result['title'], list):
                    title = ''.join([text.get('plain_text', '') for text in result['title']])
                else:
                    title = str(result['title'])
            
            documents.append({
                'id': result.get('id'),
                'title': title,
                'url': result.get('url', ''),
                'created_time': result.get('created_time', ''),
                'last_edited_time': result.get('last_edited_time', '')
            })
        
        return documents
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Notion documents: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return []

def main():
    if not NOTION_API_SECRET:
        print("Error: NOTION_API_SECRET environment variable not set")
        return
    
    print("Fetching Notion documents...")
    documents = get_notion_documents()
    
    if documents:
        print(f"\nFound {len(documents)} document(s):\n")
        for i, doc in enumerate(documents, 1):
            print(f"{i}. {doc['title']}")
            if doc['url']:
                print(f"   URL: {doc['url']}")
            print()
    else:
        print("No documents found or error occurred.")

if __name__ == '__main__':
    main()
