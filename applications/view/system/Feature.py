import json

from flask import Blueprint, request, jsonify
from applications.common.flow import Flow
from applications.common.rain import Rain
from applications.common.utils.decorators import standard_response
from applications.configuration.JsonConfig import NpEncoder

bp = Blueprint('Feature', __name__, url_prefix='/Feature')


@bp.route("/calFlowFeature", methods=['POST'])
# @standard_response
def cal_flow_feature():
    try:
        data = json.loads(request.data)
        # print("获取的参数")
        # print(data)
        floodId = data['floodId']
        floodId = int(floodId)
        stationId = data['stationId']
        stationId = int(stationId)
        startTime = data['startTime']
        endTime = data['endTime']

        sp = Flow(floodId, stationId, startTime, endTime)

        results = sp.get_FlowFeature()

        result_data = {
            "code": 200,
            "message": "成功获取流量特征数据",
            "data": results
        }

        print('results', results)
        # result_data = {
        #     "data": results,
        # }
        # # return {result_data}, 200
        # return json.dumps(result_data, cls=NpEncoder)
        return jsonify(result_data), 200
    except Exception as e:
        error_data = {
            "code": 400,
            "message": "处理请求时出错: " + str(e),
            "data": None
        }
        return jsonify(error_data), 400

@bp.route("/calRainFeature", methods=['POST'])
def cal_rain_feature():
    try:
        data = json.loads(request.data)
        # print("获取的参数")
        # print(data)
        floodId = data['floodId']
        floodId = int(floodId)
        stationId = data['stationId']
        stationId = int(stationId)
        startTime = data['startTime']
        endTime = data['endTime']

        sp = Rain(floodId, stationId, startTime, endTime)

        results = sp.get_Rain_Feature()

        print('results', results)
        #
        result_data = {
            "code": 200,
            "message": "成功获取降雨特征数据",
            "data": results
        }
        return jsonify(result_data), 200
    except Exception as e:
        error_data = {
            "code": 400,
            "message": "处理请求时出错: " + str(e),
            "data": None
        }
        return jsonify(error_data), 400
