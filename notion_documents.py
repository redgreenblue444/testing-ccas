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
    
    def extract_text_from_blocks(self, blocks: List[Dict], include_all: bool = True) -> Dict:
        """Extract text content from Notion blocks. Returns dict with content and metadata."""
        text_parts = []
        block_types = {}
        word_count = 0
        
        for block in blocks:
            block_type = block.get("type")
            block_types[block_type] = block_types.get(block_type, 0) + 1
            
            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(text)
                    word_count += len(text.split())
            elif block_type == "heading_1":
                rich_text = block.get("heading_1", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"# {text}")
                    word_count += len(text.split())
            elif block_type == "heading_2":
                rich_text = block.get("heading_2", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"## {text}")
                    word_count += len(text.split())
            elif block_type == "heading_3":
                rich_text = block.get("heading_3", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"### {text}")
                    word_count += len(text.split())
            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"• {text}")
                    word_count += len(text.split())
            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"• {text}")
                    word_count += len(text.split())
            elif block_type == "to_do":
                rich_text = block.get("to_do", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                checked = block.get("to_do", {}).get("checked", False)
                checkbox = "☑" if checked else "☐"
                if text:
                    text_parts.append(f"{checkbox} {text}")
                    word_count += len(text.split())
            elif block_type == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                language = block.get("code", {}).get("language", "")
                if text:
                    text_parts.append(f"```{language}\n{text}\n```")
                    word_count += len(text.split())
            elif block_type == "quote":
                rich_text = block.get("quote", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"> {text}")
                    word_count += len(text.split())
            elif block_type == "callout":
                rich_text = block.get("callout", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                emoji = block.get("callout", {}).get("icon", {}).get("emoji", "💡")
                if text:
                    text_parts.append(f"{emoji} {text}")
                    word_count += len(text.split())
            elif block_type == "toggle":
                rich_text = block.get("toggle", {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if text:
                    text_parts.append(f"▶ {text}")
                    word_count += len(text.split())
            elif block_type == "divider":
                text_parts.append("---")
            elif block_type == "table":
                table_data = block.get("table", {})
                text_parts.append("[Table]")
            elif block_type == "bookmark":
                url = block.get("bookmark", {}).get("url", "")
                caption = block.get("bookmark", {}).get("caption", [])
                caption_text = "".join([rt.get("plain_text", "") for rt in caption])
                if url:
                    text_parts.append(f"🔖 Bookmark: {url}")
                    if caption_text:
                        text_parts.append(f"   {caption_text}")
            elif block_type == "link_to_page":
                linked_page_id = block.get("link_to_page", {}).get("page_id", "")
                if linked_page_id:
                    text_parts.append(f"🔗 Link to page")
            elif block_type == "child_page":
                child_title = block.get("child_page", {}).get("title", "")
                if child_title:
                    text_parts.append(f"📄 Sub-page: {child_title}")
            elif block_type == "child_database":
                child_title = block.get("child_database", {}).get("title", "")
                if child_title:
                    text_parts.append(f"🗄️ Database: {child_title}")
        
        full_text = "\n".join(text_parts)
        return {
            "text": full_text,
            "word_count": word_count,
            "block_count": len(blocks),
            "block_types": block_types,
            "char_count": len(full_text)
        }
    
    def get_page_summary(self, page_id: str, max_length: int = 2000) -> Dict:
        """Get a comprehensive summary of a page's content."""
        try:
            content = self.get_page_content(page_id)
            extracted = self.extract_text_from_blocks(content["blocks"], include_all=True)
            
            text = extracted["text"]
            
            if not text.strip():
                return {
                    "summary": "No content found.",
                    "full_content": "",
                    "word_count": 0,
                    "block_count": extracted["block_count"],
                    "block_types": extracted["block_types"],
                    "char_count": 0
                }
            
            # Get full content
            full_content = text
            
            # Create a more intelligent summary
            # Try to get meaningful content (skip empty lines, bullets with no text, etc.)
            lines = []
            for line in text.split("\n"):
                stripped = line.strip()
                # Skip empty lines, standalone bullets, and empty checkboxes
                if stripped and stripped != "•" and not (stripped.startswith("☐") and len(stripped) <= 3):
                    lines.append(stripped)
            
            # Prioritize headings and paragraphs for summary
            summary_lines = []
            char_count = 0
            
            for line in lines:
                if char_count > max_length:
                    break
                # Include headings and substantial content
                if line.startswith("#") or (len(line) > 20 and not line.startswith("☐") and not line.startswith("☑")):
                    summary_lines.append(line)
                    char_count += len(line) + 1
                elif char_count < max_length * 0.3:  # Include some list items early on
                    summary_lines.append(line)
                    char_count += len(line) + 1
            
            summary = "\n".join(summary_lines)
            if len(full_content) > max_length:
                summary += "\n\n[... additional content truncated ...]"
            
            return {
                "summary": summary if summary else full_content[:max_length] + "...",
                "full_content": full_content,
                "word_count": extracted["word_count"],
                "block_count": extracted["block_count"],
                "block_types": extracted["block_types"],
                "char_count": extracted["char_count"]
            }
        except Exception as e:
            return {
                "summary": f"Error retrieving content: {str(e)}",
                "full_content": "",
                "word_count": 0,
                "block_count": 0,
                "block_types": {},
                "char_count": 0
            }


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
            print(f"\n{'='*80}")
            print(f"{i}. {page['title']}")
            print(f"{'='*80}")
            print(f"   URL: {page['url']}")
            print(f"   Created: {page['created_time']}")
            print(f"   Last Edited: {page['last_edited_time']}")
            
            page_data = client.get_page_summary(page['id'])
            
            # Print statistics
            print(f"\n   📊 Statistics:")
            print(f"      • Word count: {page_data['word_count']:,}")
            print(f"      • Character count: {page_data['char_count']:,}")
            print(f"      • Block count: {page_data['block_count']}")
            
            if page_data['block_types']:
                block_type_str = ", ".join([f"{k}: {v}" for k, v in sorted(page_data['block_types'].items(), key=lambda x: x[1], reverse=True)[:5]])
                print(f"      • Block types: {block_type_str}")
            
            print(f"\n   📝 Content Summary:")
            # Indent summary
            summary_lines = page_data['summary'].split("\n")
            for line in summary_lines:
                if line.strip():
                    print(f"      {line}")
                else:
                    print()
            
            # If there's significantly more content, mention it
            if page_data['char_count'] > 2000:
                remaining_chars = page_data['char_count'] - len(page_data['summary'])
                if remaining_chars > 500:
                    print(f"\n      [... {remaining_chars:,} more characters of content ...]")
            
            print(f"\n{'-'*80}")
        
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
