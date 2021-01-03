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
JWT_ID_ATTRIBUTE = 'email'
JWT_PRIVATE_KEY_FORMULARIUM = """
-----BEGIN RSA PRIVATE KEY-----
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
wBAg==
-----END RSA PRIVATE KEY-----
"""

JWT_PUBLIC_KEY_FORMULARIUM = """
-----BEGIN PUBLIC KEY-----
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCsL/Z6TjFnuICZB/46/1WCPWCU52tIVOWzhTdXesbMxN91p1oWdDJRQg/K4urw54SYIckcVxZkQD7aOuSeFCLGkUxbWTI4DMjz1hqjNrk4dWYMrFcaY23NFZa1yDQ7JqQ656hVakf6oO8WMXt0tTZjlFWAxqh8hsgPDFzwGA3HPS+J097DogxILWmw+6Navq8Utk0pOfcvJt6zWSRvC2NsE6Qymx4AsUQwoz9LRa/Mva8r6fmtnlCyb8uA5bw5xlCr2rS9lLoAogiv+AGBt1lft9Fkl5/dBQNgxRHBlplos7gukjDqAmzA8Nfm6f4A7ETy+tkB+cTEauZvMOFwHZVN1uNvN2OBuiztERa5QWu+kqBDGtSPTBY0uPogCG+GoVCbQRmP2p6jQ96GGpoFMHbKVptN78npPsFoH98wgHCl2vl/k5ZH51YmJPPruhhKP08dAHI+4TJ3Ffdxujopn7BBBx2OvC1o6KC4HTu1SIUa0Z0M8uIsSjrdFZBK45rEiASax5YYxPoW6EBiAAqj84z1bElgwz0ZxWlP1FcIGRNn2EzC7CytpJb6UKlIYa0MlsyavVzn/FP6bH7SjrFOc699QDlr3/Yx+a9MAlgS15yMS3uS+vliedxjwUCcMsvxog9r7RCuv0VTNoav+H5DMzPZjgpMyAU1Gc9V4VTR9OhX2w== lilithwittmann@Liliths-MacBook-Pro.local
-----END PUBLIC KEY-----
"""