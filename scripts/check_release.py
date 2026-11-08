#!/usr/bin/env python3
"""Validate release versions and distributable contents; write artifact checksums."""
import hashlib
from pathlib import Path
import re
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = (ROOT / 'VERSION').read_text().strip()
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    code = re.search(r'__version__ = "([^"]+)"', (ROOT / 'jaeger_arena/__init__.py').read_text())[1]
    assert version == project['version'] == code, 'Release versions disagree'
    assert f'EARLY ACCESS / {version}' in (ROOT / 'jaeger_arena/web/index.html').read_text()
    assert f'jaeger-arena:{version}' in (ROOT / 'compose.yaml').read_text()
    wheel = ROOT / 'dist' / f'jaeger_arena-{version}-py3-none-any.whl'
    source = ROOT / 'dist' / f'jaeger_arena-{version}.tar.gz'
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for asset in ('web/index.html', 'web/app.js', 'web/app.css', 'web/profile-cards.css',
                      'web/arena-icon.png', 'data/skills.json', 'data/worlds.json', 'data/avatar_profiles.json'):
            assert 'jaeger_arena/'+asset in names, f'Missing runtime asset: {asset}'
        assert any(n.endswith('/licenses/LICENSE') for n in names), 'Missing wheel license'
        metadata = archive.read(f'jaeger_arena-{version}.dist-info/METADATA').decode()
        assert f'Version: {version}\n' in metadata
        assert 'License-Expression: Apache-2.0' in metadata
    with tarfile.open(source) as archive:
        source_names = [n.partition('/')[2] for n in archive.getnames()]
        for required in ('LICENSE', 'README.md', 'RELEASE_NOTES.md', 'requirements.lock',
                         'run.sh', 'compose.yaml', 'deploy/Caddyfile', 'dev/docs/runtime/DEPLOYMENT.md',
                         'scripts/smoke_installed.py', 'tests/test_mcp.py'):
            assert required in source_names, f'Missing source file: {required}'
    for name in names + source_names:
        parts = Path(name).parts
        assert not any(p in ('.arena', '.local', '.venv', '.git', '.env') for p in parts), name
        assert not re.search(r'\.(sqlite3|db)(-|$)', name), name
        assert not name.endswith(('.pem', '.key')), name
    output = '\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in (wheel, source))+'\n'
    (ROOT / 'dist/SHA256SUMS').write_text(output)
    print(f'Release {version}: versions, package assets, license, source files, and artifact exclusions passed.')


if __name__ == '__main__':
    main()
