"""Content checks that allow only CRLF/LF differences in UTF-8 text files."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

TEXT_SUFFIXES = {'.py', '.json', '.csv', '.md', '.txt', '.cff', '.svg'}
TEXT_NAMES = {'.gitignore', '.gitattributes', 'LICENSE'}


def canonical_bytes(path):
    path = Path(path)
    raw = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
        raw.decode('utf-8')
        return raw.replace(b'\r\n', b'\n')
    return raw


def digest(path):
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def verify_release(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('hash_policy') != 'utf8_crlf_to_lf_otherwise_raw':
        raise ValueError('Unsupported release hash policy')
    for name, expected in manifest['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Missing or invalid release path: {name}')
        if digest(path) != expected:
            raise ValueError(f'Release content changed: {name}')
    return manifest
