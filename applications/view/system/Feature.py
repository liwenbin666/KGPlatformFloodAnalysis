import json
from flask import Blueprint, request, jsonify
from applications.common.flow import Flow
from applications.common.rain import Rain
from applications.common.utils.decorators import standard_response
from applications.configuration.JsonConfig import NpEncoder
from applications.exception.my_exception import APIException

bp = Blueprint('Feature', __name__, url_prefix='/Feature')

def make_response(data=None, message="Success", code=200):
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), code

@bp.route("/calFlowFeature", methods=['POST'])
def cal_flow_feature():
    try:
        data = json.loads(request.data)
        floodId = int(data['floodId'])
        stationId = int(data['stationId'])
        startTime = data['startTime']
        endTime = data['endTime']

        sp = Flow(floodId, stationId, startTime, endTime)
        results = sp.get_FlowFeature()

        return make_response(data=results, message="成功获取流量特征数据", code=200)
    except APIException as e:
        return make_response(message=str(e), code=e.code)
    except Exception as e:
        return make_response(message="处理请求时出错: " + str(e), code=400)

@bp.route("/calRainFeature", methods=['POST'])
def cal_rain_feature():
    try:
        data = json.loads(request.data)
        floodId = int(data['floodId'])
        stationId = int(data['stationId'])
        startTime = data['startTime']
        endTime = data['endTime']

        sp = Rain(floodId, stationId, startTime, endTime)
        results = sp.get_Rain_Feature()

        return make_response(data=results, message="成功获取降雨特征数据", code=200)
    except APIException as e:
        return make_response(message=str(e), code=e.code)
    except Exception as e:
        return make_response(message="处理请求时出错: " + str(e), code=400)
