#!/usr/bin/env python3
"""Script to verify all markdown files and internal relative links in the repository."""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def check_markdown_links():
    md_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip node_modules, .venv, dist, .git
        if any(ignored in root for ignored in ["node_modules", ".venv", "dist", ".git", ".pytest_cache"]):
            continue
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))

    print(f"Scanning {len(md_files)} markdown files for internal relative links...")
    broken_links = []
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    for md_path in md_files:
        rel_md_path = os.path.relpath(md_path, REPO_ROOT)
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = link_pattern.findall(content)
        for text, target in matches:
            # Ignore web URLs, anchors, mailto
            if target.startswith("http://") or target.startswith("https://") or target.startswith("#") or target.startswith("mailto:"):
                continue

            # Strip query params and anchor
            clean_target = target.split("#")[0].split("?")[0]
            if not clean_target:
                continue

            # Resolve relative to the markdown file's directory
            resolved_target = os.path.normpath(os.path.join(os.path.dirname(md_path), clean_target))

            if not os.path.exists(resolved_target):
                broken_links.append((rel_md_path, text, target, resolved_target))

    if broken_links:
        print(f"\n❌ Found {len(broken_links)} broken relative links:")
        for source, text, target, resolved in broken_links:
            print(f"  - In {source}: [{text}]({target}) -> Target not found: {resolved}")
        return False
    else:
        print(f"\n✅ All internal relative links verified successfully across {len(md_files)} markdown files!")
        return True

if __name__ == "__main__":
    success = check_markdown_links()
    sys.exit(0 if success else 1)
