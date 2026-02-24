#!/usr/bin/env python3
"""Debug script to understand HTML structure."""

import re
from html import unescape

file_path = r"C:\Users\anand\Downloads\Telegram Desktop\Prep_RR_Qb_Psychiatry.html"

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Find iframe srcdoc - capture everything until the closing quote
# Use a more robust pattern that handles escaped quotes
pattern = r'<iframe srcdoc="([^"]*)"'
matches = re.findall(pattern, html)
print(f'Found {len(matches)} iframes')

if matches:
    sample = matches[0]
    print(f'\nSrcdoc length: {len(sample)} chars')
    
    unescaped = unescape(sample)
    print(f'Unescaped length: {len(unescaped)} chars')
    
    # Look for questions pattern
    if 'questions' in unescaped:
        print('\n[FOUND] questions keyword in unescaped content')
        # Find questions = pattern
        q_pattern = r'questions\s*=\s*\['
        q_match = re.search(q_pattern, unescaped)
        if q_match:
            print(f'[FOUND] questions array at position {q_match.start()}')
            # Print context around it
            start = max(0, q_match.start() - 50)
            end = min(len(unescaped), q_match.end() + 200)
            print(f'\nContext around questions array:')
            print(unescaped[start:end])
    else:
        print('\n[NOT FOUND] questions keyword in unescaped content')
        # Search for alternative patterns
        if 'const questions' in sample:
            print('[FOUND] const questions in RAW srcdoc (needs double unescape)')
        if 'text' in unescaped and 'options' in unescaped:
            print('[FOUND] text and options keywords - might be question data')
