INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'accounts',
    'shares',
    'loans',
    'guarantees',
    'members',
    'directors',
    'admin_panel',
    'support',
]

AUTH_USER_MODEL = 'accounts.User'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication
LOGIN_URL = '/accounts/signin/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email backend for sending actual emails via Gmail SMTP
# NOTE: For production, EMAIL_HOST_PASSWORD MUST be stored as an environment variable.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'theibankdollars@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') # Use environment variable for security

BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')