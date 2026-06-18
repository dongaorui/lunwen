#!/usr/bin/env python3
"""Extract readable source-code snapshots from references/repos into txt files.
Run from project root: python references_txt/extract_repo_texts.py references/repos references/repo_texts
"""
from pathlib import Path
import sys

SRC_EXTS = {'.py','.sh','.md','.yaml','.yml','.json','.toml','.txt','.cfg','.ini','.ipynb','.tex'}
SKIP_DIRS = {'.git','__pycache__','.venv','venv','env','node_modules','dist','build','.mypy_cache','.pytest_cache','wandb','runs','outputs','checkpoints','models','.idea','.vscode'}
MAX_FILE_BYTES = 300_000

def should_skip(p: Path):
    return any(part in SKIP_DIRS for part in p.parts)

def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('references/repos')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('references/repo_texts')
    out.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        print(f'No such directory: {src}')
        return
    for repo in [p for p in src.iterdir() if p.is_dir()]:
        lines = [f'# Repository snapshot: {repo.name}\n']
        files = []
        for f in repo.rglob('*'):
            if f.is_file() and not should_skip(f.relative_to(repo)) and f.suffix.lower() in SRC_EXTS:
                if f.stat().st_size <= MAX_FILE_BYTES:
                    files.append(f)
        files.sort()
        lines.append(f'Total included files: {len(files)}\n')
        for f in files:
            rel = f.relative_to(repo)
            lines.append('\n' + '='*90 + f'\nFILE: {rel}\n' + '='*90 + '\n')
            try:
                lines.append(f.read_text(encoding='utf-8', errors='replace'))
            except Exception as e:
                lines.append(f'[READ ERROR] {e}\n')
        target = out / f'{repo.name}_source_snapshot.txt'
        target.write_text('\n'.join(lines), encoding='utf-8')
        print(f'Wrote {target}')

if __name__ == '__main__':
    main()
