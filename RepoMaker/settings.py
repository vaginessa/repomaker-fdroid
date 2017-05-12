"""
Django settings for RepoMaker project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import logging
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SINGLE_USER_MODE = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: change this secret key and keep it secret!
SECRET_KEY = '913d6#u8@-*#3l)spwzurd#fd77bey-6mfs5fc$a=yhnh!n4p9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
logging.getLogger().setLevel(logging.DEBUG)

# Add your host here
ALLOWED_HOSTS = ['127.0.0.1']

# Location for media accessible via the web-server such as repo icons, screenshots, etc.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = "/media/"

# Location for private data such as the repo signing key
PRIVATE_REPO_ROOT = os.path.join(BASE_DIR, 'private_repo')

# Uncomment the next line to show this notice on every page
# SITE_NOTICE = '''Maintenance ongoing. Please check back later.'''

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Uncomment and edit this, if you want to offer your users storage for their repositories
# You need to configure your web-server to serve from those locations
# DEFAULT_REPO_STORAGE = [
#     (os.path.join(BASE_DIR, 'repos'), '/repos/'),
#     ('/var/repomaker/repos', 'https://repos.example.org/'),
# ]

# Default icons
REPO_DEFAULT_ICON = "default-repo-icon.png"
APP_DEFAULT_ICON = "default-app-icon.png"

# Application definition

INSTALLED_APPS = [
    'maker.apps.MakerConfig',
    'sass_processor',
    'background_task',
    'hvad',  # model i18n
    'tinymce',
    'django.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'allauth.account',
]

SITE_ID = 1

if not SINGLE_USER_MODE:
    LOGIN_REDIRECT_URL = "/"
    # http://django-allauth.readthedocs.io/en/latest/installation.html
    INSTALLED_APPS += [
        'allauth',
        'allauth.socialaccount',
        # 'allauth.socialaccount.providers.amazon',
        # 'allauth.socialaccount.providers.baidu',
        # 'allauth.socialaccount.providers.bitbucket_oauth2',
        # 'allauth.socialaccount.providers.dropbox_oauth2',
        # 'allauth.socialaccount.providers.facebook',
        # 'allauth.socialaccount.providers.github',
        # 'allauth.socialaccount.providers.gitlab',
        # 'allauth.socialaccount.providers.google',
        # 'allauth.socialaccount.providers.linkedin_oauth2',
        'allauth.socialaccount.providers.openid',
        # 'allauth.socialaccount.providers.reddit',
        # 'allauth.socialaccount.providers.slack',
        # 'allauth.socialaccount.providers.stackexchange',
        # 'allauth.socialaccount.providers.twitter',
        # 'allauth.socialaccount.providers.weibo',
    ]
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'allauth.account.auth_backends.AuthenticationBackend',
    )
    ACCOUNT_EMAIL_VERIFICATION = "none"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'RepoMaker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'maker.context_processors.site_notice',
            ],
        },
    },
]
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'RepoMaker.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

NODE_MODULES_ROOT = os.path.join(BASE_DIR, 'node_modules')

STATICFILES_DIRS = [
    ('node_modules', NODE_MODULES_ROOT),
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

SASS_PROCESSOR_INCLUDE_DIRS = [
    NODE_MODULES_ROOT,
]

NODE_MODULES_URL = STATIC_URL + 'node_modules/'

TINYMCE_JS_URL = os.path.join(NODE_MODULES_URL, "tinymce/tinymce.js")
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'modern',
    'menubar': False,
    'toolbar': 'undo redo | bold italic | link',
    'plugins': 'autolink link lists',
    'browser_spellcheck': True,
    'statusbar': False,
}
