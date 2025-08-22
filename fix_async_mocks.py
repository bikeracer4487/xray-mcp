#!/usr/bin/env python3
"""Script to fix async mock patterns in test files."""

import re
import os

# Files to process
files = [
    "tests/test_auth_manager_comprehensive.py",
    "tests/test_client.py", 
    "tests/test_graphql_client_comprehensive.py"
]

def fix_test_method(content):
    """Fix a single test method's mock setup."""
    # Pattern to match test methods that need fixing
    pattern = r'(async def test_[^(]+\([^)]*\):.*?"""[^"]*""".*?)(mock_session = AsyncMock\(\)\s+)(mock_response = AsyncMock\([^)]*\)\s+)(mock_session\.post = MagicMock\(return_value=mock_post_context\))'
    
    def replace_func(match):
        method_start = match.group(1)
        old_session = match.group(2)
        response_setup = match.group(3)
        old_post_setup = match.group(4)
        
        # Create the fixed mock setup
        new_mock_setup = f"""mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_response
        mock_post_context.__aexit__.return_value = None
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post_context)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None"""
        
        return f"{method_start}{response_setup}        {new_mock_setup}"
    
    return re.sub(pattern, replace_func, content, flags=re.DOTALL)

# Process each file
for file_path in files:
    if not os.path.exists(file_path):
        continue
        
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find lines that need the mock_post_context definition added
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # If this line has the problematic pattern, fix the context
        if "mock_session.post = MagicMock(return_value=mock_post_context)" in line:
            # Check if mock_post_context is already defined in this method
            method_start = i
            while method_start > 0 and not lines[method_start].strip().startswith("async def test_"):
                method_start -= 1
            
            # Look for existing mock_post_context definition in this method
            has_context_def = False
            for j in range(method_start, i):
                if "mock_post_context = AsyncMock()" in lines[j]:
                    has_context_def = True
                    break
            
            # If not defined, add it before the mock_session.post line
            if not has_context_def:
                indent = "        "  # Match indentation
                new_lines.insert(-1, f"{indent}")
                new_lines.insert(-1, f"{indent}mock_post_context = AsyncMock()")
                new_lines.insert(-1, f"{indent}mock_post_context.__aenter__.return_value = mock_response")
                new_lines.insert(-1, f"{indent}mock_post_context.__aexit__.return_value = None")
                
                # Also need to add session context setup if missing
                if i + 1 < len(lines) and "mock_session.__aenter__" not in lines[i + 1]:
                    new_lines.append(f"{indent}mock_session.__aenter__.return_value = mock_session")
                    new_lines.append(f"{indent}mock_session.__aexit__.return_value = None")
        
        i += 1
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))

print("Fixed async mock patterns in all test files.")