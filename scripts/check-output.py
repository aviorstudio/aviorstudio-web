"""Verify the product-owned static output contract."""
from pathlib import Path

for name in ('index', 'devtools/index', 'games/index'):
    page = Path('dist')/(name+'.html')
    if not page.is_file() or not page.stat().st_size:
        raise SystemExit(f'{page} is missing or empty')
javascript = sorted(Path('dist').rglob('*.js'))
if javascript:
    raise SystemExit('Static output contains JavaScript: '+', '.join(map(str, javascript)))
print('All three pages exist and no JavaScript is shipped')
