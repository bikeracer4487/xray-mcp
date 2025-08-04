#!/usr/bin/env python3
"""
Script to download and convert Xray GraphQL API documentation to markdown files.
Version 2 with improved HTML parsing and markdown conversion.
"""

import os
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin
import time
import re

BASE_URL = "https://us.xray.cloud.getxray.app/doc/graphql/"

# Documentation categories and their pages
DOCS = {
    "queries": [
        "getfolder", "gettest", "gettests", "getexpandedtest", "getexpandedtests",
        "getcoverableissue", "getcoverableissues", "getdataset", "getdatasets",
        "getprecondition", "getpreconditions", "gettestset", "gettestsets",
        "gettestplan", "gettestplans", "gettestexecution", "gettestexecutions",
        "gettestrun", "gettestrunbyid", "gettestruns", "gettestrunsbyid",
        "getstepstatus", "getstatus", "getstatuses", "getstepstatuses",
        "getprojectsettings", "getissuelinktypes"
    ],
    "mutations": [
        "createfolder", "deletefolder", "renamefolder", "movefolder",
        "addteststofolder", "addissuestofolder", "removetestsfromfolder",
        "removeissuesfromfolder", "createtest", "updatetesttype",
        "updateunstructuredtestdefinition", "updategherkintestdefinition",
        "deletetest", "addteststep", "updateteststep", "removeteststep",
        "removeallteststeps", "addpreconditionstotest", "removepreconditionsfromtest",
        "updatetestfolder", "updatepreconditionfolder", "addtestsetstotest",
        "removetestsetsfromtest", "addtestplanstotest", "removetestplansfromtest",
        "addtestexecutionstotest", "removetestexecutionsfromtest", "createprecondition",
        "updateprecondition", "deleteprecondition", "addteststoprecondition",
        "removetestsfromprecondition", "createtestset", "deletetestset",
        "addteststotestset", "removetestsfromtestset", "createtestplan",
        "deletetestplan", "addteststotestplan", "removetestsfromtestplan",
        "addtestexecutionstotestplan", "removetestexecutionsfromtestplan",
        "createtestexecution", "deletetestexecution", "addteststotestexecution",
        "removetestsfromtestexecution", "addtestenvironmentstotestexecution",
        "removetestenvironmentsfromtestexecution", "resettestrun", "updatetestrunstatus",
        "updatetestruncomment", "updatetestrun", "adddefectstotestrun",
        "removedefectsfromtestrun", "addevidencetotestrun", "removeevidencefromtestrun",
        "updatetestrunstep", "addevidencetotestrunstep", "removeevidencefromtestrunstep",
        "adddefectstotestrunstep", "removedefectsfromtestrunstep", "updatetestrunstepcomment",
        "updatetestrunstepstatus", "updatetestrunexamplestatus", "updateiterationstatus",
        "settestruntimer"
    ],
    "scalars": ["boolean", "float", "int", "json", "string"],
    "enums": ["directivelocation", "typekind"],
    "objects": [
        "actionfolderresult", "adddefectsresult", "addevidenceresult",
        "addpreconditionsresult", "addtestenvironmentsresult", "addtestexecutionsresult",
        "addtestplansresult", "addtestsetsresult", "addtestsresult", "attachment",
        "changes", "coverableissue", "coverableissueresults", "coveragestatus",
        "createpreconditionresult", "createtestexecutionresult", "createtestplanresult",
        "createtestresult", "createtestsetresult", "customstepfield", "dataset",
        "datasetrow", "evidence", "example", "expandedstep", "expandedtest",
        "expandedtestresults", "folder", "folderresults", "issuelinktype",
        "parameter", "precondition", "preconditionresults", "projectsettings",
        "projectsettingstestcoverage", "projectsettingstestruncustomfield",
        "projectsettingstestruncustomfields", "projectsettingsteststepfield",
        "projectsettingsteststepsettings", "projectsettingstesttype", "removedefectsresult",
        "removeevidenceresult", "result", "resultsembedding", "resultsexample",
        "resultsstep", "simplefolderresults", "status", "step", "stepstatus",
        "test", "testexecution", "testexecutionresults", "testplan", "testplanresults",
        "testresults", "testrun", "testruncustomfieldvalue", "testruncustomstepfield",
        "testruniteration", "testruniterationresults", "testruniterationstepresult",
        "testruniterationstepresults", "testrunparameter", "testrunprecondition",
        "testrunpreconditionresults", "testrunresults", "testrunstep", "testset",
        "testsetresults", "teststatustype", "testtype", "testversion", "testversionresults",
        "updateiterationstatusresult", "updatetestrunexamplestatusresult", "updatetestrunresult",
        "updatetestrunstepresult", "updatetestrunstepstatusresult", "updateteststepresult",
        "xrayhistoryentry", "xrayhistoryresults", "directive", "enumvalue", "field",
        "inputvalue", "schema", "type"
    ],
    "input_objects": [
        "attachmentdatainput", "attachmentinput", "attachmentoperationsinput",
        "createstepinput", "customfieldinput", "customstepfieldinput",
        "foldersearchinput", "preconditionfoldersearchinput", "testrundefectoperationsinput",
        "testrunevidenceoperationsinput", "testtypeinput", "testwithversioninput",
        "updatepreconditioninput", "updatepreconditiontypeinput", "updatestepinput",
        "updatetestrunstepinput", "updatetesttypeinput"
    ],
    "directives": ["cost", "deprecated", "include", "skip"]
}

def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_page(url):
    """Download a page and return its content."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def clean_filename(filename):
    """Clean filename for safe file system usage."""
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def html_to_markdown(element):
    """Convert HTML element to markdown with better formatting."""
    if element is None:
        return ""
    
    markdown_lines = []
    
    def process_element(elem, depth=0):
        """Recursively process HTML elements."""
        if isinstance(elem, NavigableString):
            text = str(elem).strip()
            if text:
                return text
            return ""
        
        if not isinstance(elem, Tag):
            return ""
        
        # Handle different tags
        tag_name = elem.name.lower()
        
        if tag_name == 'h1':
            return f"# {elem.get_text(strip=True)}\n"
        elif tag_name == 'h2':
            return f"## {elem.get_text(strip=True)}\n"
        elif tag_name == 'h3':
            return f"### {elem.get_text(strip=True)}\n"
        elif tag_name == 'h4':
            return f"#### {elem.get_text(strip=True)}\n"
        elif tag_name == 'p':
            return f"{elem.get_text(strip=True)}\n"
        elif tag_name == 'pre' or tag_name == 'code':
            # Handle code blocks
            code_text = elem.get_text(strip=False)
            if elem.parent and elem.parent.name == 'pre':
                return ""  # Skip if already handled by parent
            if tag_name == 'pre':
                return f"```\n{code_text}\n```\n"
            else:
                return f"`{code_text}`"
        elif tag_name == 'ul':
            items = []
            for li in elem.find_all('li', recursive=False):
                items.append(f"- {li.get_text(strip=True)}")
            return '\n'.join(items) + '\n'
        elif tag_name == 'ol':
            items = []
            for i, li in enumerate(elem.find_all('li', recursive=False), 1):
                items.append(f"{i}. {li.get_text(strip=True)}")
            return '\n'.join(items) + '\n'
        elif tag_name == 'table':
            # Simple table handling
            rows = []
            for tr in elem.find_all('tr'):
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text(strip=True))
                if cells:
                    rows.append(' | '.join(cells))
            if rows:
                return '\n'.join(rows) + '\n'
            return ""
        elif tag_name == 'br':
            return '\n'
        elif tag_name in ['strong', 'b']:
            return f"**{elem.get_text(strip=True)}**"
        elif tag_name in ['em', 'i']:
            return f"*{elem.get_text(strip=True)}*"
        elif tag_name == 'a':
            text = elem.get_text(strip=True)
            href = elem.get('href', '')
            if href and not href.startswith('#'):
                return f"[{text}]({href})"
            return text
        else:
            # For other tags, process children
            result = []
            for child in elem.children:
                child_text = process_element(child, depth + 1)
                if child_text:
                    result.append(child_text)
            return ' '.join(result)
    
    # Process all children of the main element
    for child in element.children:
        text = process_element(child)
        if text and text.strip():
            markdown_lines.append(text)
    
    # Join lines and clean up extra whitespace
    markdown = '\n'.join(markdown_lines)
    # Remove multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    return markdown.strip()

def extract_and_convert_content(html):
    """Extract main content and convert to markdown."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find the main content area
    main_content = soup.select_one('body > main')
    if not main_content:
        main_content = soup.find('main')
    
    if not main_content:
        # Try to find content div
        main_content = soup.find('div', class_='content')
    
    if not main_content:
        return None, "Could not find main content area"
    
    # Look for specific sections we want to extract
    sections = []
    
    # Title
    title_elem = main_content.find(['h1', 'h2'])
    if title_elem:
        title = title_elem.get_text(strip=True)
    else:
        title = "Unknown"
    
    # Schema definition
    schema_section = main_content.find(text=re.compile('GraphQL Schema definition'))
    if schema_section:
        schema_parent = schema_section.find_parent()
        if schema_parent:
            next_pre = schema_parent.find_next('pre')
            if next_pre:
                sections.append("## GraphQL Schema Definition\n\n```graphql\n" + next_pre.get_text(strip=False) + "\n```")
    
    # Arguments/Fields section
    args_section = main_content.find(text=re.compile('Arguments|Fields'))
    if args_section:
        args_parent = args_section.find_parent()
        if args_parent:
            args_content = []
            current = args_parent.find_next_sibling()
            while current and current.name not in ['h2', 'h3']:
                if current.name == 'p' or current.get_text(strip=True):
                    args_content.append(html_to_markdown(current))
                current = current.find_next_sibling()
            if args_content:
                sections.append("## Arguments\n\n" + '\n'.join(args_content))
    
    # Example section
    example_section = main_content.find(text=re.compile('Example'))
    if example_section:
        example_parent = example_section.find_parent()
        if example_parent:
            example_content = []
            current = example_parent.find_next_sibling()
            while current and current.name not in ['h2', 'h3']:
                if current.name == 'pre':
                    example_content.append("```graphql\n" + current.get_text(strip=False) + "\n```")
                elif current.get_text(strip=True):
                    example_content.append(html_to_markdown(current))
                current = current.find_next_sibling()
            if example_content:
                sections.append("## Example\n\n" + '\n\n'.join(example_content))
    
    # If we didn't find specific sections, just convert the whole content
    if not sections:
        sections.append(html_to_markdown(main_content))
    
    return title, '\n\n'.join(sections)

def download_all_docs():
    """Download all documentation pages."""
    output_dir = "/Users/douglas.mason/Documents/GitHub/xray-importer/docs/xray-docs"
    ensure_dir(output_dir)
    
    # Create index file
    index_content = "# Xray GraphQL API Documentation\n\n"
    index_content += "This directory contains the complete documentation for Xray's GraphQL API.\n\n"
    
    for category, pages in DOCS.items():
        category_dir = os.path.join(output_dir, category)
        ensure_dir(category_dir)
        
        print(f"\nProcessing {category}...")
        index_content += f"\n## {category.replace('_', ' ').title()}\n\n"
        
        for page in pages:
            # Construct URL
            if category in ["enums"] and page in ['directivelocation', 'typekind']:
                url = urljoin(BASE_URL, f"{page}.spec.html")
            elif category == "objects" and page in ['directive', 'enumvalue', 'field', 'inputvalue', 'schema', 'type']:
                url = urljoin(BASE_URL, f"{page}.spec.html")
            else:
                url = urljoin(BASE_URL, f"{page}.doc.html")
            
            print(f"  Downloading {page}...")
            
            # Download the page
            html_content = download_page(url)
            if html_content is None:
                continue
            
            # Extract and convert content
            title, markdown_content = extract_and_convert_content(html_content)
            
            if title is None:
                print(f"    Warning: Could not extract content from {page}")
                continue
            
            # Add header
            final_content = f"# {title}\n\n"
            final_content += f"**Category:** {category.replace('_', ' ').title()}\n"
            final_content += f"**Source:** {url}\n\n"
            final_content += markdown_content
            
            # Save to file
            filename = f"{clean_filename(page)}.md"
            filepath = os.path.join(category_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            print(f"    Saved to {filename}")
            
            # Add to index
            index_content += f"- [{title}]({category}/{filename})\n"
            
            # Be polite to the server
            time.sleep(0.5)
    
    # Save index file
    index_path = os.path.join(output_dir, "README.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("\nDownload complete!")
    print(f"Index saved to {index_path}")

if __name__ == "__main__":
    download_all_docs()