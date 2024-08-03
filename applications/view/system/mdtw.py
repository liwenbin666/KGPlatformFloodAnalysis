import json

from flask import Blueprint, render_template, request, jsonify
from applications.common.utils.database import DBUtils
from applications.common.mdtw import MdtwMatch
from applications.exception.my_exception import APIException
from applications.configuration.JsonConfig import NpEncoder
bp = Blueprint('mdtw', __name__, url_prefix='/mdtw')

def make_response(data=None, message="Success", code=200):
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), code

@bp.route('/', methods=['GET'])
def test():
    try:
        db = DBUtils()
        res = db.test_conn()
        data = {
            "data": res
        }
        return make_response(data=data, message="Database connection successful", code=200)
    except APIException as e:
        return make_response(message=str(e), code=e.code)
    except Exception as e:
        return make_response(message="Error testing database connection: " + str(e), code=400)

@bp.get('/match')
def mdtw_match():
    try:
        flood_id = request.args.get("flood_id")
        flood_id = int(flood_id)
        weights = request.args.get("weights")
        weights = eval(weights)  # String转list
        mm = MdtwMatch(flood_id, weights)
        res = mm.mdtw()
        return make_response(data=res, message="Successfully matched MDTW", code=200)
    except APIException as e:
        return make_response(message=str(e), code=e.code)
    except Exception as e:
        return make_response(message="Error during MDTW match: " + str(e), code=400)
