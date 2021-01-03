from settings.settings import *
from os import environ
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': environ.get('RDS_DB_HOST'),
        'NAME': environ.get('RDS_DB_NAME'),
        'USER': environ.get('RDS_DB_USER'),
        'PASSWORD': environ.get('RDS_DB_PASSWORD'),
    },
}


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

AWS_EB_DEFAULT_REGION = "eu-central-1"
# your aws access key id
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
# your aws access key
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
# queue name to use - queues that don't exist will be created automatically

SECRET_KEY = environ.get('DJANGO_SECRET_KEY')

STATIC_ROOT = "/static/"
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_REGION_NAME = 'eu-central-1'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')


# TODO: move this to config
JWT_ISSUER = 'FORMULARIUM'
JWT_AUTH_DISABLED = False
JWT_ID_ATTRIBUTE = 'email'
JWT_PRIVATE_KEY_FORMULARIUM = """
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
"""

JWT_PUBLIC_KEY_FORMULARIUM = """
-----BEGIN RSA PUBLIC KEY-----
MIICCgKCAgEApZDxqhI8O93V0LGwAiQqYR1n2PPeby7DbvrE3yd4zWgw5Rxe3Snm
zXH2t+Q0O3OSsH5y19ZeDgfyRX74REr+bPW0Mkg99POAJWmXZF6XyWEKWETJ4I+/
sK5jySOMOA6Bc+eSPoPtQTjUdI7zLk/XXPlzid6LveRqPinj4LpO4yHmN6tFRQPG
6dZ/gIshCONoS/YZLeYUhQIGSuL7zNJTldcXhKRXcZ5iqW+v4DlNtuzCLGlZtLnu
33H9cHmW9kWxbdMB0a6Jf/x8I8X3g3Cbu1pcDduDrRtDgkrYq4UDFT07UlpRiGZ3
lHtK/48aYu0CnsglVEIpku4S85IAOYWTz9D1yjIkTWXauaywGXsUPcf2/mlEMicl
XonynoY0ixR9IxbWCBr2XxeiyCaYx0xzP9dPrVIyhZRgbZXfM5CHRexlUWwWAifv
fJfEjDVq76SqwYr70Ta1aMRIYMb90ojmaHyRKOR+KGHAJb2T32sC9FNMb0ELksN1
vZRahYhUtDBUZLvf9iBVXEGOiVCj1J12AvoGz6mX8IYWqpD9ldl+i17PeD+rW5+T
gsNj/IzY2AnvIp4+rcozzqaOt10KvdItEO9JWOEdqNI8fJ+M6MREFLg+driUtw4C
ODTozIIfl6GpJzbHxSWcKdmp348IogXHFd8TQgdXEtO1jQ3Npo82IIcCAwEAAQ==
-----END RSA PUBLIC KEY-----
"""



OAUTH2_PROVIDER = {
    'SCOPES': {
        'admin': 'Administrator',
        'administrative-staff': 'Administrative Staff',
    },
}