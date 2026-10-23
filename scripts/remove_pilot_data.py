"""Operator-only removal of ALL local runtime data, with no backup or content reads.

Never imported by a web view. Defaults to inventory. The operator must stop the
web application and every writer before confirming. Cannot erase provider copies.
"""
import argparse
import os
import shutil
from pathlib import Path

CONFIRMATION = 'RETIRAR_DATOS_DEL_PILOTO'


class RemovalBlocked(Exception):
    pass


def inventory(root, environment):
    root = Path(root).absolute()
    directory = root / 'var'
    if root.is_symlink() or directory.is_symlink() or root.resolve() != root:
        raise RemovalBlocked('Se rechazan rutas enlazadas. No se ha iniciado el borrado.')
    for key in ('DATABASE_PATH', 'PRIVATE_MEDIA_ROOT', 'PRACTICE_DATABASE_PATH'):
        if environment.get(key):
            candidate = Path(environment[key]).absolute()
            if not candidate.is_relative_to(directory) or not candidate.resolve().is_relative_to(directory):
                raise RemovalBlocked('Hay una ruta de datos configurada fuera de var. Requiere revisión separada; no se ha iniciado el borrado.')
    if not directory.exists():
        return directory, 0
    if not directory.is_dir():
        raise RemovalBlocked('var no es un directorio. No se ha iniciado el borrado.')
    files = 0
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise RemovalBlocked('Hay enlaces simbólicos dentro de var. Requiere revisión separada; no se ha iniciado el borrado.')
        if not path.is_dir() and not path.is_file():
            raise RemovalBlocked('Hay entradas especiales dentro de var. No se ha iniciado el borrado.')
        if path.is_file():
            files += 1
    return directory, files


def remove(root, environment, *, confirm='', site_disabled=False):
    if confirm != CONFIRMATION or not site_disabled:
        raise RemovalBlocked('Se exige confirmar la retirada completa y declarar detenida la web y todos los procesos escritores.')
    directory, count = inventory(root, environment)
    if directory.exists():
        for child in directory.iterdir():
            # Recheck immediately before deletion; the stopped service is required.
            if child.is_symlink():
                raise RemovalBlocked('Se ha detectado un cambio de rutas. Detén la operación y revisa el resultado.')
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        os.chmod(directory, 0o700)
        if any(directory.iterdir()):
            raise RemovalBlocked('Quedan archivos o se han recreado. Mantén la web detenida y revisa los procesos.')
    return count


def main():
    parser = argparse.ArgumentParser(description='Retira todos los datos operativos locales de este piloto. Sin copia previa automática.')
    parser.add_argument('--confirm', default='')
    parser.add_argument('--site-disabled', action='store_true', help='Declara desactivada la web y detenidos TODOS los procesos escritores.')
    args = parser.parse_args()
    root = Path(__file__).absolute().parent.parent
    try:
        _, count = inventory(root, os.environ)
        print('Alcance: TODO var de este repositorio: bases y diarios SQLite, cuentas, sesiones, alumnado, responsables, importaciones, adjuntos, copias y prácticas.')
        print('Se conservan código, entorno virtual y archivos externos. No se crea ninguna copia nueva.')
        print(f'Archivos locales encontrados: {count}. No se muestran nombres ni contenidos.')
        if not args.confirm:
            print('SOLO INVENTARIO: no se ha eliminado nada.')
            return 0
        removed = remove(root, os.environ, confirm=args.confirm, site_disabled=args.site_disabled)
        print(f'Retirada local completada: {removed} archivos; var sin archivos restantes.')
        print('Mantén la web desactivada. No se han comprobado logs externos, descargas ni copias del proveedor. No acredita borrado físico.')
        return 0
    except (OSError, RemovalBlocked):
        # Exceptions may contain personal filenames; never print them.
        print('Operación bloqueada o incompleta. Mantén la web desactivada. Revisa rutas, permisos y procesos según docs/RETIRAR_DATOS_REALES.md.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
