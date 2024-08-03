import json
from flask import request
from werkzeug.exceptions import HTTPException
from applications.common.utils.http_status_codes import HTTPStatusCodes

class APIException(HTTPException):
    code = HTTPStatusCodes.INTERNAL_SERVER_ERROR  # 默认状态码为500
    msg = "Something went wrong!"  # 默认错误消息

    def __init__(self, msg=None, code=None, headers=None):
        self.code = code if code is not None else self.code
        self.msg = msg if msg is not None else self.msg
        super().__init__(description=self.msg, response=None)

    def get_body(self, environ=None, *args, **kwargs):
        """返回JSON格式的响应体"""
        body = {
            "msg": self.msg,
            "code": self.code,
            "request": f"{request.method} {self._get_request_path()}"
        }
        return json.dumps(body)

    def get_headers(self, environ=None, *args, **kwargs):
        """返回响应头，默认是JSON格式"""
        return [('Content-Type', 'application/json')]

    @staticmethod
    def _get_request_path():
        """获取请求的URL路径，不包括查询参数"""
        return request.path
