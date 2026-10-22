"""Compila los catálogos locales. Requiere requirements-dev.txt; no contacta con servicios externos."""
from pathlib import Path
import polib

root=Path(__file__).resolve().parent.parent
for path in (root/'locale').glob('*/LC_MESSAGES/*.po'):
    catalog=polib.pofile(path)
    missing=[entry.msgid for entry in catalog if not entry.obsolete and (not entry.msgstr or 'fuzzy' in entry.flags)]
    if missing: raise SystemExit(f'{path}: {len(missing)} mensajes sin traducir o sin revisar.')
    catalog.save_as_mofile(path.with_suffix('.mo'))
    print(f'{path.relative_to(root)}: {len(catalog)} mensajes compilados.')
