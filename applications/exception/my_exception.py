'''
自定义全局异常类
'''
import json
from flask import request
from werkzeug.exceptions import HTTPException

class APIException(HTTPException):
    code = 500
    msg = "something wrong!"
    error_code = 999

    def __init__(self, msg=None, code=None, error_code=None, headers=None):
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        if msg:
            self.msg = msg
        super().__init__(msg, None)

    def get_body(self, *args, **kwargs):
        body = dict(
            msg=self.msg,
            error_code=self.error_code,
            request=request.method + ' ' + self.get_url_no_parm()
        )
        text = json.dumps(body)
        return text

    # def get_headers(self, environ=None):
    #     return [('Content-Type', 'application/json')]
    def get_headers(self, *args, **kwargs):
        """Ensure this method accepts any additional arguments."""
        return [('Content-Type', 'application/json')]

    @staticmethod
    def get_url_no_parm():
        full_path = str(request.full_path)
        main_path = full_path.split('?')
        return main_path[0]
