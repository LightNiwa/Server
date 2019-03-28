import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

VERSION_CODE = 22
PRIVATE_PATH = '/git/LightReader-Web/private'
API_URL = 'https://106.187.44.157'
API_HEADER = {
    'X-Api-Key': '31971AA043E72E305B48E006ED0AECC5',
    'X-Api-Time': '1432010950993',
    'User-Agent': 'LKNovel-Android-0.0.1',
    'Host': 'www.linovel.com',
    'Connection': 'keep-alive'
}

FLASK_ASSETS_USE_CDN = True
CDN_DOMAIN = 'cdn.ltype.me'
CDN_HTTPS = True
CDN_TIMESTAMP = False

SECRET_KEY = ''

DATABASE_URI = ''
DATABASE_CONNECT_OPTIONS = {}

UPLOAD_FOLDER = '/static/image/upload/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


QN_ACCESS_KEY = ''
QN_SECRET_KEY = ''
QN_BUCKET_DOMAIN = ''

del os
