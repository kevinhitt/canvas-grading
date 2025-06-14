#!/usr/bin/env python3
"""
Markdown to HTML Converter with Beautiful Styling
Converts all .md files in a folder to HTML with embedded CSS styling
"""

import os
import sys
import glob
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: 'markdown' library not found.")
    print("Install it with: pip install markdown")
    sys.exit(1)

# Beautiful CSS template with the requested color #2C68AA
CSS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2C68AA;
            margin-bottom: 0.5em;
            margin-top: 1em;
            font-weight: 600;
        }}
        
        h1 {{
            font-size: 2.5em;
            border-bottom: 3px solid #2C68AA;
            padding-bottom: 0.3em;
            margin-top: 0;
        }}
        
        h2 {{
            font-size: 2em;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 0.2em;
        }}
        
        h3 {{
            font-size: 1.5em;
        }}
        
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        
        a {{
            color: #2C68AA;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.3s ease;
        }}
        
        a:hover {{
            border-bottom-color: #2C68AA;
            color: #1e4a7a;
        }}
        
        ul, ol {{
            margin-left: 2em;
            margin-bottom: 1em;
        }}
        
        li {{
            margin-bottom: 0.5em;
            white-space: pre-line;
        }}
        
        li p {{
            margin-bottom: 0.5em;
            white-space: pre-line;
        }}
        
        blockquote {{
            border-left: 4px solid #2C68AA;
            margin: 1.5em 0;
            padding: 1em 2em;
            background-color: #f8f9fa;
            font-style: italic;
            color: #555;
        }}
        
        code {{
            background-color: #f1f3f4;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            color: #d73a49;
        }}
        
        pre {{
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: #333;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 0.8em;
            text-align: left;
        }}
        
        th {{
            background-color: #2C68AA;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        hr {{
            border: none;
            height: 2px;
            background: linear-gradient(to right, #2C68AA, #e9ecef);
            margin: 2em 0;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin: 1em 0;
        }}
        
        .footer {{
            margin-top: 3em;
            padding-top: 2em;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            <p>Generated from Markdown • <a href="#top">Back to top</a></p>
        </div>
    </div>
</body>
</html>
"""

def preprocess_markdown(md_content):
    """
    Preprocess markdown content to better preserve line breaks and formatting
    """
    lines = md_content.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        processed_lines.append(line)
        
        # Add extra spacing after numbered list items if the next line isn't empty
        if (line.strip() and 
            i < len(lines) - 1 and 
            lines[i + 1].strip() and 
            not lines[i + 1].startswith((' ', '\t')) and
            (line.strip().startswith(tuple(f'{j}.' for j in range(1, 100))) or
             line.strip().startswith(tuple(f'{j})' for j in range(1, 100))))):
            # If next line is also a numbered item or starts new content, add spacing
            next_line = lines[i + 1].strip()
            if (next_line.startswith(tuple(f'{j}.' for j in range(1, 100))) or
                next_line.startswith(tuple(f'{j})' for j in range(1, 100))) or
                next_line.startswith('#')):
                processed_lines.append('')
    
    return '\n'.join(processed_lines)

def convert_markdown_to_html(md_file_path, output_dir=None):
    """
    Convert a single Markdown file to HTML with embedded CSS
    """
    try:
        # Read the markdown file
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Preprocess the markdown for better formatting
        md_content = preprocess_markdown(md_content)
        
        # Convert markdown to HTML with line break preservation
        md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'nl2br'])
        html_content = md.convert(md_content)
        
        # Get the title (first h1 or filename)
        title = Path(md_file_path).stem.replace('_', ' ').replace('-', ' ').title()
        
        # Generate the complete HTML
        full_html = CSS_TEMPLATE.format(
            title=title,
            content=html_content
        )
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / f"{Path(md_file_path).stem}.html"
        else:
            output_path = Path(md_file_path).with_suffix('.html')
        
        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        return output_path
        
    except Exception as e:
        print(f"Error converting {md_file_path}: {e}")
        return None

def convert_folder(input_folder, output_folder=None):
    """
    Convert all Markdown files in a folder to HTML
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    # Create output folder if specified
    if output_folder:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    
    # Find all markdown files
    md_files = list(input_path.glob('*.md')) + list(input_path.glob('*.markdown'))
    
    if not md_files:
        print(f"No Markdown files found in '{input_folder}'")
        return
    
    print(f"Found {len(md_files)} Markdown file(s) to convert:")
    
    converted_files = []
    
    for md_file in md_files:
        print(f"Converting: {md_file.name}")
        
        if output_path:
            html_file = convert_markdown_to_html(md_file, output_path)
        else:
            html_file = convert_markdown_to_html(md_file)
        
        if html_file:
            converted_files.append(html_file)
            print(f"  → {html_file}")
    
    print(f"\nConversion complete! {len(converted_files)} file(s) converted.")
    
    if converted_files:
        print(f"\nHTML files saved to: {output_path or input_path}")

def main():
    """
    Main function - handle command line arguments
    """
    if len(sys.argv) < 2:
        print("Markdown to HTML Converter")
        print("Usage:")
        print("  python md_to_html.py <input_folder> [output_folder]")
        print("\nExamples:")
        print("  python md_to_html.py ./docs")
        print("  python md_to_html.py ./markdown_files ./html_output")
        return
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_folder(input_folder, output_folder)

if __name__ == "__main__":
    main()