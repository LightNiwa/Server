from flask import json

ERR_SUCCESS = 0x00
ERR_FAILED = 0x01


def wrap_resp(data, err_code=ERR_SUCCESS, msg=""):
    return dumps({'data': data, 'errCode': err_code, 'msg': msg})


def dumps(data):
    return json.dumps(data, ensure_ascii=False), 200, {'ContentType': 'application/json'}
