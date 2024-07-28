from functools import wraps

from applications.common.utils.responses import response_result


def standard_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
            # 如果返回是 (data, status, message) 格式的元组
            return response_result(*result)
        return response_result(result)
    return wrapper
