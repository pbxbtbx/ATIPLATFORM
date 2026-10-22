"""Importadores locales: datos sin ejecutar macros, instrucciones ni enlaces."""
import csv
import io
import re
import zipfile
from xml.etree import ElementTree as ET
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

MAX_UPLOAD = 2 * 1024 * 1024


def read_upload(upload):
    data = upload.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise ValidationError(_('El archivo supera el límite de 2 MB.'))
    return data


def parse_csv(data, kind):
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError:
        raise ValidationError(_('Guarda el CSV con codificación UTF-8.'))
    delimiter = ';' if ';' in text.split('\n')[0] else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    required = {'nombre'} if kind == 'students' else {'titulo', 'inicio', 'duracion_minutos'}
    allowed = {'nombre','nombre_preferido','nacimiento'} if kind == 'students' else required | {'objetivos','materiales','actividades','numero'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames) or set(reader.fieldnames) - allowed or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValidationError(_('Cabeceras no válidas. Utiliza la plantilla descargable.'))
    rows = []
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValidationError(_('Cada fila debe tener el mismo número de columnas.'))
        if any(v.strip() for v in row.values()):
            rows.append({k:v.strip() for k,v in row.items()})
        if len(rows) > 200:
            raise ValidationError(_('El límite es de 200 registros por importación.'))
    if not rows:
        raise ValidationError(_('No hay registros para importar.'))
    return rows


def parse_docx(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries)>300 or sum(i.file_size for i in entries)>12*1024*1024 or any('vbaProject' in i.filename for i in entries):
                raise ValueError()
            xml = archive.read('word/document.xml')
            if b'\x00' in xml or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                raise ValueError()
            root = ET.fromstring(xml)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError, RuntimeError, NotImplementedError):
        raise ValidationError(_('El archivo no es un DOCX válido o excede los límites de seguridad.'))
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    lines = [''.join(t.text or '' for t in p.iter(ns+'t')).strip() for p in root.iter(ns+'p')]
    lines = [line for line in lines if line]
    if not lines:
        raise ValidationError(_('El documento no contiene texto legible.'))
    headings = ['Preparar antes de la clase','Estructura de la sesión','Presentación inicial','Ladrillos que trabajamos','Retos desbloqueables','Errores previsibles y respuesta docente','Atención a la diversidad','Plan B','Cierre','Qué observar para el seguimiento']
    def section(name):
        if name not in lines: return ''
        start=lines.index(name)+1
        end=next((i for i in range(start,len(lines)) if lines[i] in headings),len(lines))
        return '\n'.join(lines[start:end])
    duration=next((int(m.group(1)) for line in lines if (m:=re.fullmatch(r'(\d{1,3})\s*min',line))),None)
    number=re.search(r'(?:Ficha Docente|Ficha)\s*(\d+)',lines[0],re.I)
    # Formato desconocido: conservar todo el texto para revisión, sin adivinar secciones.
    return {'title':lines[1] if len(lines)>1 and number else lines[0], 'number':int(number.group(1)) if number else 1,
            'duration':duration, 'goals':section('Ladrillos que trabajamos'),
            'materials':section('Preparar antes de la clase'),
            'planned':'\n\n'.join(h+'\n'+section(h) for h in headings if section(h)),
            'diversity':section('Atención a la diversidad'),
            'source':'\n'.join(lines)}
