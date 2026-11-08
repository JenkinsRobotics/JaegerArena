#!/usr/bin/env python3
"""Check the static site and active documentation using only the standard library."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs'
errors = []
checked = 0


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.refs = []
        self.h1_count = 0
        self.has_title = False
        self.has_lang = False
        self.has_description = False
        self.has_viewport = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                errors.append(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs['id'])
        self.h1_count += tag == 'h1'
        self.has_title |= tag == 'title'
        self.has_lang |= tag == 'html' and bool(attrs.get('lang'))
        self.has_description |= tag == 'meta' and attrs.get('name') == 'description' and bool(attrs.get('content'))
        self.has_viewport |= tag == 'meta' and attrs.get('name') == 'viewport'
        for field in ('src', 'href'):
            if attrs.get(field):
                self.refs.append(attrs[field])
        if tag == 'img' and 'alt' not in attrs:
            errors.append(f"Missing image alternative text: {attrs.get('src')}")


def check_ref(source, ref, ids=None):
    global checked
    parsed = urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        # Repository links on the site should resolve to actual tracked content.
        prefix = 'https://github.com/JenkinsRobotics/JaegerArena/blob/master/'
        if ref.startswith(prefix):
            target = ROOT / unquote(urlsplit(ref[len(prefix):]).path)
            checked += 1
            if not target.is_file():
                errors.append(f'{source.relative_to(ROOT)}: missing repository target {ref}')
        return
    checked += 1
    if parsed.path:
        if source.is_relative_to(SITE) and source.suffix == '.html' and parsed.path.startswith('/'):
            errors.append(f'{source.name}: absolute site path breaks project Pages hosting: {ref}')
        target = (source.parent / unquote(parsed.path)).resolve()
        if not target.exists():
            errors.append(f'{source.relative_to(ROOT)}: missing target {ref}')
        elif source.suffix == '.html' and not target.is_relative_to(SITE):
            errors.append(f'{source.name}: target will not be published: {ref}')
    elif parsed.fragment and ids is not None and unquote(parsed.fragment) not in ids:
        errors.append(f'{source.name}: missing fragment {ref}')


def main():
    index = SITE / 'index.html'
    page = Page()
    page.feed(index.read_text())
    if page.h1_count != 1:
        errors.append('The page needs exactly one h1')
    if not all((page.has_title, page.has_lang, page.has_description, page.has_viewport)):
        errors.append('Missing title, language, description, or viewport metadata')
    for ref in page.refs:
        check_ref(index, ref, page.ids)
    active_docs = [ROOT / 'README.md', ROOT / 'AGENTS.md', SITE / 'SITE.md', SITE / 'BRAND.md', *sorted((ROOT / 'dev/docs').rglob('*.md'))]
    for path in active_docs:
        content = path.read_text()
        for ref in re.findall(r'\[[^\]\n]+\]\(([^)\s]+)\)', content):
            check_ref(path, ref)
    text_assets = [p for p in sorted((SITE / 'assets').rglob('*'))
                   if p.is_file() and p.suffix in {'.css', '.js', '.svg', '.html', '.json', '.txt', '.md'}]
    for path in [index, *active_docs, *text_assets]:
        if re.search(r'\{\{[A-Za-z_]+\}\}', path.read_text()):
            errors.append(f'{path.relative_to(ROOT)}: unfilled template placeholder')
    if not (SITE / '.nojekyll').is_file():
        errors.append('Missing docs/.nojekyll')
    if errors:
        print('\n'.join(f'ERROR: {error}' for error in errors), file=sys.stderr)
        return 1
    print(f'Site checks passed: {checked} local/repository links, metadata, IDs, image alt text, and active-doc placeholders.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
