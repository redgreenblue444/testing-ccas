# Notion Documents Lister

This script lists and summarizes all Notion documents that you own or have access to through your Notion integration.

## Setup

1. **Create a Notion Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "Document Lister")
   - Copy the "Internal Integration Token"

2. **Share pages with your integration:**
   - Open each Notion page you want to access
   - Click the "..." menu → "Add connections"
   - Select your integration

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key:**
   ```bash
   export NOTION_API_KEY='your_token_here'
   ```

5. **Run the script:**
   ```bash
   python notion_documents.py
   ```

## Output

The script will display:
- List of all accessible Notion pages
- Title and URL for each page
- Creation and last edited timestamps
- A summary of each page's content
