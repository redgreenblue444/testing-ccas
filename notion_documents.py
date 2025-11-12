#!/usr/bin/env python3
"""
Script to list and summarize Notion documents owned by the user.
Requires NOTION_API_KEY environment variable to be set.
"""

import os
import requests
from typing import List, Dict, Optional
import json


class NotionClient:
    """Client for interacting with Notion API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.notion.com/v1"
    
    def search_pages(self, filter_type: str = "page") -> List[Dict]:
        """Search for pages in Notion."""
        url = f"{self.base_url}/search"
        payload = {
            "filter": {
                "property": "object",
                "value": filter_type
            }
        }
        
        all_results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            all_results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return all_results
    
    def get_page_content(self, page_id: str) -> Dict:
        """Get content blocks of a page."""
        url = f"{self.base_url}/blocks/{page_id}/children"
        
        all_blocks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            params = {}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return {"blocks": all_blocks}
    
    def extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Extract text content from Notion blocks."""
        text_parts = []
        
        for block in blocks:
            block_type = block.get("type")
            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(text)
            elif block_type == "heading_1":
                rich_text = block.get("heading_1", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"# {text}")
            elif block_type == "heading_2":
                rich_text = block.get("heading_2", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"## {text}")
            elif block_type == "heading_3":
                rich_text = block.get("heading_3", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"### {text}")
            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"• {text}")
            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"• {text}")
            elif block_type == "to_do":
                rich_text = block.get("to_do", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                checked = block.get("to_do", {}).get("checked", False)
                checkbox = "☑" if checked else "☐"
                if text:
                    text_parts.append(f"{checkbox} {text}")
            elif block_type == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"```\n{text}\n```")
            elif block_type == "quote":
                rich_text = block.get("quote", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"> {text}")
        
        return "\n".join(text_parts)
    
    def get_page_summary(self, page_id: str, max_length: int = 500) -> str:
        """Get a summary of a page's content."""
        try:
            content = self.get_page_content(page_id)
            text = self.extract_text_from_blocks(content["blocks"])
            
            if not text.strip():
                return "No content found."
            
            # Simple summary: take first few sentences or truncate
            sentences = text.split(".")
            summary_parts = []
            char_count = 0
            
            for sentence in sentences:
                if char_count + len(sentence) > max_length:
                    break
                summary_parts.append(sentence.strip())
                char_count += len(sentence) + 1
            
            summary = ". ".join(summary_parts)
            if len(text) > max_length:
                summary += "..."
            
            return summary if summary else text[:max_length] + "..."
        except Exception as e:
            return f"Error retrieving content: {str(e)}"


def get_owned_pages(client: NotionClient) -> List[Dict]:
    """Get pages that the user owns (created by them)."""
    all_pages = client.search_pages(filter_type="page")
    
    # Filter pages - in Notion API, pages you own typically have created_by matching your user
    # For now, we'll return all accessible pages (you can filter further if needed)
    owned_pages = []
    
    for page in all_pages:
        # Check if page is accessible and get basic info
        page_info = {
            "id": page.get("id"),
            "title": None,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", ""),
            "created_by": page.get("created_by", {}).get("id", ""),
        }
        
        # Extract title from properties
        properties = page.get("properties", {})
        title_prop = None
        
        # Look for title property (can be named "title", "Name", etc.)
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_prop = prop_value
                break
        
        if title_prop:
            title_rich_text = title_prop.get("title", [])
            if title_rich_text:
                page_info["title"] = "".join([rt.get("plain_text", "") for rt in title_rich_text])
        
        # Fallback: try to get title from page object itself
        if not page_info["title"]:
            # Some pages have title in the page object
            if "title" in page:
                page_info["title"] = page["title"]
            else:
                page_info["title"] = "Untitled"
        
        owned_pages.append(page_info)
    
    return owned_pages


def main():
    """Main function to list and summarize Notion documents."""
    # Try multiple environment variable names for the API key/secret
    # Check all possible variations
    api_key = None
    env_vars_to_check = [
        "notion_api_secret",
        "NOTION_API_SECRET", 
        "NOTION_API_KEY",
        "notion_api_key",
        "NOTION_SECRET",
        "notion_secret"
    ]
    
    for var_name in env_vars_to_check:
        api_key = os.getenv(var_name)
        if api_key:
            print(f"Using API key from: {var_name}")
            break
    
    if not api_key:
        # Try checking all environment variables for anything containing 'notion'
        all_env = dict(os.environ)
        notion_vars = {k: v[:10] + "..." if len(v) > 10 else v 
                      for k, v in all_env.items() 
                      if 'notion' in k.lower()}
        
        if notion_vars:
            print(f"Found Notion-related env vars: {list(notion_vars.keys())}")
            # Try the first one
            api_key = list(notion_vars.values())[0]
        else:
            print("Error: Notion API secret/key not found.")
            print(f"Checked for: {', '.join(env_vars_to_check)}")
            print("\nTo use this script:")
            print("1. Create a Notion integration at https://www.notion.so/my-integrations")
            print("2. Copy the Internal Integration Token")
            print("3. Share the pages you want to access with your integration")
            print("4. Set the token: export notion_api_secret='your_token_here'")
            print("5. Run this script again")
            return
    
    try:
        client = NotionClient(api_key)
        print("Fetching your Notion pages...\n")
        
        owned_pages = get_owned_pages(client)
        
        if not owned_pages:
            print("No pages found. Make sure:")
            print("1. Your integration token is correct")
            print("2. You've shared the pages with your integration")
            return
        
        print(f"Found {len(owned_pages)} page(s):\n")
        print("=" * 80)
        
        for i, page in enumerate(owned_pages, 1):
            print(f"\n{i}. {page['title']}")
            print(f"   URL: {page['url']}")
            print(f"   Created: {page['created_time']}")
            print(f"   Last Edited: {page['last_edited_time']}")
            print(f"\n   Summary:")
            summary = client.get_page_summary(page['id'])
            # Indent summary
            for line in summary.split("\n"):
                print(f"   {line}")
            print("\n" + "-" * 80)
        
    except requests.exceptions.HTTPError as e:
        print(f"Error accessing Notion API: {e}")
        if e.response.status_code == 401:
            print("Authentication failed. Check your NOTION_API_KEY.")
        elif e.response.status_code == 404:
            print("Resource not found. Make sure pages are shared with your integration.")
        else:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
