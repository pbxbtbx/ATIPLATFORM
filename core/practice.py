"""Almacén SQLite independiente: solo dos identidades ficticias por cuenta."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .curriculum import AREAS

PUPILS=[('alpha',_('Aprendiz ficticio A')),('beta',_('Aprendiz ficticio B'))]
TASKS={
 'design_3d':[_('Dibujar una idea'),_('Crear una forma básica'),_('Combinar volúmenes'),_('Ajustar medidas'),_('Preparar una pieza imprimible'),_('Revisar el laminado'),_('Probar un prototipo'),_('Explicar una mejora')],
 'robotics':[_('Identificar componentes'),_('Montar una estructura'),_('Conectar un actuador'),_('Leer un sensor'),_('Programar una respuesta'),_('Probar el mecanismo'),_('Depurar un fallo'),_('Explicar el funcionamiento')],
 'games':[_('Crear un personaje'),_('Programar el movimiento'),_('Añadir un objeto'),_('Situar elementos'),_('Detectar un contacto'),_('Reutilizar una secuencia'),_('Definir una victoria'),_('Crear y explicar una regla nueva')],
 'ethical_ai':[_('Reconocer un uso de IA'),_('Distinguir datos y opiniones'),_('Comprobar una respuesta'),_('Identificar un sesgo'),_('Proteger datos personales'),_('Revisar una fuente'),_('Proponer un uso responsable'),_('Explicar límites y decisiones')],
 'mobile_apps':[_('Definir una necesidad'),_('Dibujar una pantalla'),_('Añadir un botón'),_('Programar un evento'),_('Organizar la navegación'),_('Probar accesibilidad'),_('Corregir un error'),_('Presentar una app útil')],
}


def initial():
    return {'students':{key:{a['key']:[] for a in AREAS} for key,label in PUPILS},'history':[]}


@contextmanager
def connection():
    path=Path(settings.PRACTICE_DATABASE_PATH).resolve()
    primary=Path(settings.DATABASES['default']['NAME']).resolve()
    if path==primary or (path.exists() and primary.exists() and os.path.samefile(path,primary)):raise ValidationError(_('La base de práctica debe estar separada de la base principal.'))
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=20,isolation_level=None)
    try:
        os.chmod(path,0o600)
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tables-{'practice_runs'}:raise ValidationError(_('La base de práctica contiene tablas ajenas. Usa un archivo independiente.'))
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if version==0:db.executescript((Path(__file__).parent/'practice_migrations'/'0001_initial.sql').read_text())
        elif version!=1:raise ValidationError(_('La versión de la base de práctica no es compatible.'))
        yield db
    finally:db.close()


def read(owner):
    with connection() as db:
        row=db.execute('SELECT version,payload FROM practice_runs WHERE owner=?',(owner,)).fetchone()
    return (row[0],json.loads(row[1])) if row else (0,initial())


def save(owner,expected,student,area,reached,reset=False):
    updates=reached if student=='both' and isinstance(reached,dict) else {student:reached}
    if not reset and (area not in TASKS or set(updates)!=set(dict(PUPILS)) or any(not isinstance(ids,list) or len(ids)!=len(set(ids)) or set(ids)-{f'R{n}' for n in range(1,9)} for ids in updates.values())):
        raise ValidationError(_('Selección de práctica no válida.'))
    with connection() as db:
        try:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT version,payload FROM practice_runs WHERE owner=?',(owner,)).fetchone()
            version=row[0] if row else 0
            if version!=expected:raise ValidationError(_('La práctica ha cambiado en otra pestaña. Recarga antes de guardar.'))
            state=json.loads(row[1]) if row else initial()
            if reset:state=initial()
            else:
                for pupil,ids in updates.items():
                    if state['students'][pupil][area]!=ids:
                        state['students'][pupil][area]=ids
                        state['history'].append({'student':pupil,'area':area,'reached':ids,'date':timezone.now().isoformat()})
                state['history']=state['history'][-100:]
            db.execute('INSERT INTO practice_runs(owner,version,payload,updated_at) VALUES(?,?,?,?) ON CONFLICT(owner) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_at=excluded.updated_at',
                       (owner,version+1,json.dumps(state),timezone.now().isoformat()))
            db.execute('COMMIT')
        except Exception:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
