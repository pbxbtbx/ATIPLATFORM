"""Read-only, bounded security evidence. Never read educational records or execute tools."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from django.conf import settings
from django.utils.translation import gettext as _

MANIFEST = 'security-manifest.json'
SCOPES = ('core', 'config', 'templates', 'static', 'scripts', '.github', 'locale', 'docs')
ROOT_FILES = ('manage.py', 'requirements.txt', 'requirements-dev.txt', 'requirements-security.txt', 'README.md', '.env.example')
MAX_FILES = 3000


def source_files(root):
    files = set()
    for scope in SCOPES:
        if (root / scope).is_symlink():
            raise ValueError('symlink')
        for path in (root / scope).rglob('*'):
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('symlink')
            if path.is_file():
                files.add(path.relative_to(root).as_posix())
                if len(files) > MAX_FILES:
                    raise ValueError('limit')
    return sorted(files | {name for name in ROOT_FILES if (root / name).is_file()})


def fingerprint(root):
    result = {}
    for name in source_files(root):
        path = root / name
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('limit')
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def integrity():
    try:
        root = Path(settings.BASE_DIR)
        path = root / MANIFEST
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError('manifest')
        raw = path.read_bytes()
        expected = json.loads(raw)
        if expected['schema'] != 1 or not isinstance(expected['files'], dict) or len(expected['files']) > MAX_FILES:
            raise ValueError('manifest')
        actual = fingerprint(root)
        changed = sum(expected['files'].get(k) != actual.get(k) for k in set(expected['files']) | set(actual))
        return {'status': 'warning' if changed else 'ok', 'count': changed, 'digest': hashlib.sha256(raw).hexdigest()}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unknown', 'count': None, 'digest': ''}


def report_path():
    return Path(settings.BASE_DIR) / 'var' / 'security' / (settings.ENVIRONMENT + '.json')


def scan_evidence(check):
    """Only allowlisted aggregate values; never render raw scanner output."""
    try:
        path = report_path()
        if path.is_symlink() or path.stat().st_size > 16384:
            raise ValueError('report')
        data = json.loads(path.read_bytes())
        stamp = datetime.fromisoformat(data['created_at'])
        age = datetime.now(timezone.utc) - stamp
        if data['schema'] != 1 or not timedelta(0) <= age <= timedelta(hours=24):
            raise ValueError('stale')
        if check['status'] != 'ok' or data['manifest_digest'] != check['digest'] or data['environment'] != settings.ENVIRONMENT:
            raise ValueError('source')
        scans = []
        for key, label in [('bandit', _('Análisis estático de Python')), ('dependencies', _('Vulnerabilidades conocidas en dependencias'))]:
            item = data[key]
            if item['status'] not in ('ok', 'warning', 'unknown') or type(item['count']) is not int or not 0 <= item['count'] <= 100000:
                raise ValueError('scan')
            if (item['status'] == 'ok' and item['count'] != 0) or (item['status'] == 'warning' and item['count'] == 0):
                raise ValueError('inconsistent')
            scans.append({'label': label, 'status': item['status'], 'count': item['count']})
        return {'available': True, 'created_at': stamp, 'scans': scans}
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        return {'available': False}


def dependency_drift():
    from importlib.metadata import version, PackageNotFoundError
    try:
        lines = (Path(settings.BASE_DIR) / 'requirements.txt').read_text().splitlines()
        for line in lines:
            if not line.strip() or line.startswith('#'):
                continue
            name, expected = line.split('==')
            if version(name) != expected:
                return False
        return bool(lines)
    except (OSError, ValueError, PackageNotFoundError):
        return False


def runtime_checks():
    checks = []
    def add(label, good):
        checks.append({'label': label, 'status': 'ok' if good else 'warning'})
    add(_('Dependencias instaladas coinciden con las versiones declaradas'), dependency_drift())
    add(_('Depuración desactivada'), not settings.DEBUG)
    add(_('Clave de aplicación propia y suficientemente larga'), len(settings.SECRET_KEY) >= 50 and not settings.SECRET_KEY.startswith('local-development'))
    add(_('Hosts explícitos sin comodín'), bool(settings.ALLOWED_HOSTS) and all(h and '*' not in h for h in settings.ALLOWED_HOSTS))
    add(_('Cookies de sesión y CSRF solo por HTTPS'), settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE)
    add(_('Redirección a HTTPS'), settings.SECURE_SSL_REDIRECT)
    add(_('HSTS configurado'), settings.SECURE_HSTS_SECONDS > 0)
    add(_('Cookies de sesión protegidas frente a JavaScript'), settings.SESSION_COOKIE_HTTPONLY)
    add(_('Protección contra marcos y detección de contenido'), settings.X_FRAME_OPTIONS == 'DENY' and settings.SECURE_CONTENT_TYPE_NOSNIFF)
    add(_('Middleware CSRF activo'), 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE)
    add(_('Entorno de producción para datos reales'), settings.ENVIRONMENT == 'production')
    return checks
