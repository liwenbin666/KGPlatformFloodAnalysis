import json
import numpy as np
from flask import Blueprint, request, jsonify
from applications.common.slice import SliceFlood
from applications.exception.my_exception import APIException
from datetime import datetime
from pandas import Timestamp
from applications.configuration.JsonConfig import NpEncoder

bp = Blueprint('slice', __name__, url_prefix='/slice')


def make_response(data=None, message="Success", code=200):
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), code


def convert_numpy(data):
    """
    递归地将numpy类型和Timestamp类型转换为原生Python类型和字符串
    """
    if isinstance(data, dict):
        return {convert_numpy(key): convert_numpy(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy(element) for element in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (np.integer, np.int64)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64)):
        return float(data)
    elif isinstance(data, Timestamp):
        return data.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return data


def convert_dates(data):
    """
    递归地将日期时间字符串转换为指定格式的字符串
    """
    date_format_in = "%a, %d %b %Y %H:%M:%S GMT"
    date_format_out = "%Y-%m-%d %H:%M:%S"

    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_dates(value)
    elif isinstance(data, list):
        data = [convert_dates(element) for element in data]
    elif isinstance(data, str):
        try:
            parsed_date = datetime.strptime(data, date_format_in)
            data = parsed_date.strftime(date_format_out)
        except ValueError:
            pass  # 如果字符串不是日期格式，则保持原样

    return data


@bp.route("/sliceFlood", methods=['POST'])
def Slice():
    try:
        data = json.loads(request.data)

        stationId = data['stationId']
        stationId = int(stationId)

        startTime = data['startTime']
        endTime = data['endTime']

        height = data['height']
        height = int(height)

        distance = data['distance']
        distance = int(distance)

        duration = data['duration']
        duration = int(duration)

        sf = SliceFlood(stationId, startTime, endTime, height, distance, duration)
        slice_res = sf.slice_flood()
        print("结果数据：")
        print(slice_res)

        # 在返回之前，转换numpy类型为原生Python类型
        converted_res = convert_numpy(slice_res)

        # 转换日期格式
        converted_res = convert_dates(converted_res)

        return make_response(data=converted_res, message="成功获取分段数据", code=200)
    except APIException as e:
        return make_response(message=str(e), code=e.code)
    except Exception as e:
        return make_response(message="处理请求时出错: " + str(e), code=400)
