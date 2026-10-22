import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv('APP_ENV', 'development')
if ENVIRONMENT not in ('development','testing','staging','production','demo'):
    raise RuntimeError('APP_ENV no reconocido')
# Public demo/staging must never default to an interactive traceback.
DEBUG = os.getenv('DEBUG', '1' if ENVIRONMENT in ('development', 'testing') else '0') == '1' and ENVIRONMENT != 'production'
# Security review: local fallback only; production rejects it; dashboard warns for public demo.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-development-only-do-not-deploy')  # nosec B105
# Public production rejects the documented local placeholder.
if ENVIRONMENT == 'production' and SECRET_KEY == 'local-development-only-do-not-deploy':  # nosec B105
    raise RuntimeError('Configure DJANGO_SECRET_KEY antes de producción')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS = ['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','core.middleware.UserLanguageMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','core.middleware.MaintenanceMiddleware','core.middleware.SafeErrorMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.context.navigation']}}]
WSGI_APPLICATION = 'config.wsgi.application'
(BASE_DIR/'var').mkdir(exist_ok=True)
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('DATABASE_PATH',str(BASE_DIR/'var'/('db.sqlite3' if ENVIRONMENT=='development' else ENVIRONMENT+'.sqlite3'))),'OPTIONS':{'timeout':20,'transaction_mode':'IMMEDIATE'}}}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'}]
LANGUAGE_CODE = 'es'
LANGUAGES = [('es','Español'),('en','English')]
LOCALE_PATHS = [BASE_DIR/'locale']
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR/'static']
STATIC_ROOT = BASE_DIR/'staticfiles'
# Explicit private paths allow changing environment without moving existing records/files.
MEDIA_ROOT = Path(os.getenv('PRIVATE_MEDIA_ROOT', str(BASE_DIR/'var'/'private'/ENVIRONMENT)))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if ENVIRONMENT == 'production' or os.getenv('HTTPS_ONLY', '0') == '1':
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
DATA_UPLOAD_MAX_MEMORY_SIZE = 12*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2*1024*1024

SESSION_COOKIE_AGE = 8*60*60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700

# Lote ODS acotado a 300 alumnos y dos responsables; límite finito para su revisión.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 6000

# Prácticas ficticias: archivo independiente; nunca apunta a la base educativa.
PRACTICE_DATABASE_PATH = Path(os.getenv('PRACTICE_DATABASE_PATH', str(BASE_DIR/'var'/'practice'/(ENVIRONMENT+'.sqlite3'))))
