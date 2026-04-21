#!/usr/bin/env python3
"""
Quick script to update README.md with latest job opportunities
"""
import pandas as pd
import os

def update_readme_from_csv():
    """Update README.md with jobs from CSV"""
    try:
        # Read CSV
        df = pd.read_csv('april_2026_opportunities.csv')
        
        if df.empty:
            print("❌ CSV is empty")
            return False
        
        # Convert to markdown
        markdown_table = df.to_markdown(index=False)
        
        # Read README
        with open('README.md', 'r', encoding='utf-8', errors='ignore') as f:
            readme_content = f.read()
        
        # Find markers
        start = readme_content.find('<!--START_SECTION:workfetch-->')
        end = readme_content.find('<!--END_SECTION:workfetch-->')
        
        if start == -1 or end == -1:
            print("❌ Markers not found in README.md")
            return False
        
        # Create new content
        new_content = (
            f"{readme_content[:start]}"
            f"<!--START_SECTION:workfetch-->\n{markdown_table}\n"
            f"{readme_content[end:]}"
        )
        
        # Write back
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ README.md updated with {len(df)} jobs!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    update_readme_from_csv()
