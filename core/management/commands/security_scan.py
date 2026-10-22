"""Fixed external tools run ONLY by an operator/CI, never by a web request."""
import json
import os
# Security review: fixed CLI tools only; no web caller or shell.
import subprocess  # nosec B404
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.security_review import integrity, report_path, dependency_drift


def run_scan(module, arguments, parser):
    try:
        # Fixed modules and arguments, no request data, no shell execution.
        result = subprocess.run(  # nosec B603
            [sys.executable, '-m', module, *arguments], cwd=settings.BASE_DIR,
            capture_output=True, timeout=180, check=False)
        # Output is discarded, not logged or exposed on the website.
        if len(result.stdout) > 8 * 1024 * 1024:
            raise ValueError('limit')
        data = json.loads(result.stdout)
        count = parser(data)
        if result.returncode not in (0, 1) or type(count) is not int or count < 0 or count > 100000:
            raise ValueError('scan')
        if (result.returncode == 0) != (count == 0):
            raise ValueError('exit')
        return {'status': 'warning' if count else 'ok', 'count': count}
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        return {'status': 'unknown', 'count': 0}


def bandit_count(data):
    if data.get('errors') or not isinstance(data['results'], list):
        raise ValueError('incomplete')
    return len(data['results'])


def dependency_count(data):
    if not isinstance(data['dependencies'], list):
        raise ValueError('incomplete')
    if any('skip_reason' in item for item in data['dependencies']):
        raise ValueError('skipped')
    return sum(len(item['vulns']) for item in data['dependencies'])


class Command(BaseCommand):
    help = 'Análisis fijos sin datos educativos; pip-audit consulta metadatos públicos de dependencias.'
    def handle(self, *args, **options):
        check = integrity()
        cache = report_path().parent / 'audit-cache'
        cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        bandit = run_scan('bandit', ['-r', 'core', 'config', 'scripts', '-x', 'core/migrations,core/test', '-f', 'json', '-q'], bandit_count)
        dependencies = run_scan('pip_audit', ['-r', 'requirements.txt', '--no-deps', '--disable-pip', '--progress-spinner', 'off', '--cache-dir', str(cache), '-f', 'json'], dependency_count)
        # Bind results only if files stayed identical throughout the scan.
        final = integrity()
        valid = check['status'] == final['status'] == 'ok' and check['digest'] == final['digest']
        data = {'schema': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                'environment': settings.ENVIRONMENT, 'manifest_digest': check['digest'] if valid else '',
                'bandit': bandit, 'dependencies': dependencies}
        path = report_path()
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump(data, output)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        for name in ('bandit', 'dependencies'):
            self.stdout.write(f'{name}: {data[name]["status"]}; hallazgos={data[name]["count"]}')
        if not valid or not dependency_drift() or any(data[k]['status'] != 'ok' for k in ('bandit', 'dependencies')):
            raise CommandError('Revisión necesaria. No se ha certificado seguridad; consulta el procedimiento de diagnóstico.')
