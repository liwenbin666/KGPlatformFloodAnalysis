from flask import make_response, jsonify


def response_result(data, status=200, message='OK'):
    response_body = {
        'status': status,
        'message': message,
        'data': data
    }
    response = make_response(jsonify(response_body), status)
    return response
