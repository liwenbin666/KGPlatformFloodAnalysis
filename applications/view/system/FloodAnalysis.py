import json
import pandas as pd

from flask import Blueprint, request
from applications.common.flow import Flow
from applications.common.rain import Rain
from applications.common.slice import SliceFlood
from applications.configuration.JsonConfig import NpEncoder


bp = Blueprint('FloodAnalysis', __name__, url_prefix='/FloodAnalysis')

@bp.route("/sliceAndCalFeature", methods=['POST'])
def slice_calFeature():
    # 从请求中获取参数
    data = json.loads(request.data)
    # print("获取的参数")
    # print(data)
    floodId = data['floodId']
    basinId = data['basinId']
    stationId = data['stationId']
    startTime = data['startTime']
    endTime = data['endTime']
    height = 400
    distance = 72


    # 进行场次划分
    sf = SliceFlood(stationId, startTime, endTime, height, distance)
    # peaks = sf.slice_flood()
    slice_res = sf.slice_flood()
    print("划分结果是：{}".format(slice_res))
    # 初始化results列表
    results = []
    for flood in slice_res:
        # print("每场洪水：{}".format(flood))
        startTime = slice_res[flood]['start_date']
        startTime = str(startTime)
        endTime = slice_res[flood]['end_date']
        endTime = str(endTime)
        floodId = slice_res[flood]['flood_id']
        print("场次ID：{}".format(floodId)+" 开始时间：{}".format(startTime)+" 结束时间：{}".format(endTime))

        # 进行特征提取
        sp = Flow(floodId, stationId, startTime, endTime)
        curr_res = sp.get_FlowFeature()
        curr_rain = Rain(floodId, stationId, startTime, endTime)
        curr_rain_res = curr_rain.get_Rain_Feature()
        # 合并两个字典
        combined_res = curr_res.copy()  # 先复制 curr_res，以免修改原字典
        combined_res.update(curr_rain_res)  # 使用 update 方法将 curr_rain_res 合并到 combined_res 中
        print("本场特征值提取结果：{}".format(combined_res))
        print("--------------------------------------------------------------------")

        # 将本场特征值提取结果加入到results列表中
        results.append(combined_res)

    # # 进行特征提取
    # sp = Flow(floodId, stationId, startTime, endTime)
    # results = sp.get_FlowFeature()

    print('results', results)
    result_data = {
        "features": results
    }
    return json.dumps(result_data, cls=NpEncoder)
