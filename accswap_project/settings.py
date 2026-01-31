from pathlib import Path
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

# For development, keep DEBUG = True.
# For a live website, you MUST change this to DEBUG = False and set ALLOWED_HOSTS.
DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = 'django-insecure-this-is-a-safe-default-for-development'

# --- Application Definition ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_totp',
    # Our local app
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CORS Middleware must be placed high up, especially before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # OTP middleware must be after auth middleware
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'accswap_project.urls'
WSGI_APPLICATION = 'accswap_project.wsgi.application'

TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',],},},]

# --- Database ---
DATABASES = { 'default': { 'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3' } }

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},]

# --- Internationalization (Indian Model) ---
LANGUAGE_CODE = 'en-IN'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CORS Configuration ---
# This is the crucial part that gives permission for the two servers to talk.
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

# --- Django REST Framework & JWT Settings ---
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',)}
SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),}

# --- Payment Gateway Configuration ---
# IMPORTANT: Replace these with your actual TEST keys from your dashboards.
STRIPE_PUBLISHABLE_KEY = 'your_stripe_publishable_key_here'
STRIPE_SECRET_KEY = 'your_stripe_secret_key_here'
STRIPE_WEBHOOK_SECRET = 'your_stripe_webhook_secret_here'

RAZORPAY_KEY_ID = 'rzp_test_SASTfIIFKzeqgF'
RAZORPAY_KEY_SECRET = 'S0HiTT8cHAuagECsUNQqC4bZ'
RAZORPAY_WEBHOOK_SECRET = 'your_razorpay_webhook_secret_here'


# ... at the end of settings.py ...

import os

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]