INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    
    # Custom apps
    'accounts',
    'accounts_amor108.apps.AccountsAmor108Config',
    'admin_panel',
    'amor108',
    'audit',
    'contributions',
    'dashboard',
    'directors',
    'governance',
    'guarantees',
    'investments',
    'loans',
    'members',
    'members_amor108',
    'messaging',
    'notifications',
    'payments',
    'pools.apps.PoolsConfig',
    'profiles',
    'profits',
    'reports',
    'shares',
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

CSRF_TRUSTED_ORIGINS = ["https://webbankglobal.onrender.com/",]