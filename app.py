import subprocess

from flask import Flask, request, g
import requests
import json
from applications import create_app

app = create_app()

if __name__ == '__main__':

    app.run()

# app = Flask(__name__)
#
# @app.route('/flood_get', methods=['POST'])
# def flood_get():
#     stcd = request.form.get('stcd')
#     step = 3600 #写死？
#     endTime = request.form.get('endTime')
#     startTime = request.form.get('startTime')
#
#     data = {
#         "endTime": endTime,
#         "startTime": startTime,
#         "stcd": stcd,
#         "step": step
#     }
#
#     header = {
#         "appCode": "ed47024c55d248fe914ce22be29ff649"
#     }
#     url = 'http://jcglwg.ybzx.mwr.cn/metaserver-yun/api/server/api/standard/river'
#
#     response = requests.post(url, headers=header, json=data)
#
#     if response.status_code == 200:
#         response_data = response.json()
#         flood_data = {}
#         for station_code, station_data in response_data['data'].items():
#             flood_data[station_code] = []
#             for data_point in station_data:
#                 flood_data[station_code].append({
#                     "q":data_point['q'],
#                     "time":data_point['tm']
#                 })
#         print(flood_data)
#         g.flood = flood_data
#         run()
#
#         return "200"
#     else:
#         print("HTTP请求失败，状态码："+str(response.status_code))
#
#
# @app.route('/flood_feature', methods=['POST'])
# def feature():
#     wkt = request.form.get('wkt')
#     rainfall_file_path = request.form.get('file_path')
#     start_time = request.form.get('start_time')
#     end_time = request.form.get('end_time')
#
#
#     return "200"
#
# def run():
#     subprocess.run(["python", "analyse.py", g.flood])


