import json

from flask import Blueprint, render_template, request, jsonify
from applications.common.utils.database import DBUtils
from applications.common.mdtw import MdtwMatch
from applications.configuration.JsonConfig import NpEncoder
bp = Blueprint('mdtw', __name__, url_prefix='/mdtw')

@bp.route('/', methods=['GET'])
def test():
    db = DBUtils()
    res = db.test_conn()
    data = {
        "data":res
    }
    return jsonify(data)

@bp.get('/match')
def mdtw_match():
    flood_id = request.args.get("flood_id")
    flood_id = int(flood_id)
    weights = request.args.get("weights")
    weights = eval(weights)  # String转list
    mm = MdtwMatch(flood_id,weights)
    res = mm.mdtw()
    return res
