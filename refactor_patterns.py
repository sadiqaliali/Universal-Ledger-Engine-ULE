import os
import re

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the PATTERNS dictionary start and end
    start_tag = 'PATTERNS = {'
    end_tag = '}'
    
    start_idx = content.find(start_tag)
    if start_idx == -1:
        return
        
    # Find the matching closing bracket
    bracket_count = 0
    end_idx = -1
    for i in range(start_idx + len(start_tag) - 1, len(content)):
        if content[i] == '{':
            bracket_count += 1
        elif content[i] == '}':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == -1:
        return

    patterns_str = content[start_idx + len(start_tag):end_idx-1]
    
    # Entries: r"regex": ("SQL", [indices]) OR "SQL"
    entries = re.findall(r'(r"[^"]+"):\s*(?:\(([^)]+)\)|("[^"]+"))', patterns_str)
    
    new_patterns_entries = []
    
    for regex_part, tuple_part, str_part in entries:
        regex = regex_part.strip().strip('r').strip('"').strip("'")
        
        # SQL template
        if tuple_part:
            template_match = re.search(r'"([^"]+)"|\'([^\']+)\'', tuple_part)
            if template_match:
                template = template_match.group(1) or template_match.group(2)
            else:
                template = "SELECT * FROM {0}" # Fallback
        else:
            template = str_part.strip().strip('"').strip("'")
            
        # 1. Count capture groups in regex
        try:
            num_groups = re.compile(regex).groups
        except Exception:
            num_groups = len(re.findall(r'(?<!\)\((?!\?\:)', regex))
            
        # 2. Find indices used as identifiers {n}
        used_indices = set(int(n) for n in re.findall(r'\{(\d+)\}', template))
        
        # 3. All other groups are parameters
        param_indices = [i for i in range(num_groups) if i not in used_indices]
        
        # If legacy, replace values with ?
        if not tuple_part:
            for i in param_indices:
                template = template.replace('{' + str(i) + '}', '?')
        
        # Clean LIKE
        template = template.replace("'%?%'", "?").replace("%?%", "?").replace("LIKE '%{1}%'", "LIKE ?")
        
        new_entry = f'    {regex_part}:\n        ("{template}", {param_indices}),'
        new_patterns_entries.append(new_entry)

    new_block = '\n\n'.join(new_patterns_entries)
    final_content = content[:start_idx] + f'PATTERNS = {{\n{new_block}\n}}' + content[end_idx:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

patterns_dir = 'ule/ai/patterns'
for filename in os.listdir(patterns_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        refactor_file(os.path.join(patterns_dir, filename))
