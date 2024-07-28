from datetime import datetime

from scipy import signal
from applications.exception.my_exception import APIException
import pandas as pd
from applications.common.utils.database import DBUtils
import json



class Flow():

    def __init__(self, floodId, stationId, startTime, endTime):

        self.floodId = floodId
        self.stationId = stationId
        self.startTime = startTime
        self.endTime = endTime

        self.data = None
        self.flowList = None
        self.timeList = None

        # 特征值
        self.peakPattern = None  # 洪峰模式
        self.durationFlood = None  # 洪水持续时间
        self.peakFlood = None  # 流量峰值
        self.peakFloodTime = None  # 最大流量时间
        self.totalFlood = None  # 洪水总量
        self.startLastTime = None  # 洪水开始多久到达峰值（小时）
        self.endLastTime = None  # 洪水达到峰值后持续多久（小时）
        self.resultState = {}

        # 数据库操作工具
        self.db_utils = DBUtils()

        # 指定CSV文件的路径
        # csv_file_path = 'D:\postgraduate\project\PatternLibrary\data\\flow_data.csv'
        # self.data = pd.read_csv(csv_file_path, header=0, names=['Time', 'FlowValue'])
        # print("csv文件里的数据是")
        # print(self.data)

        # SQL查询
        sql = f"""
                SELECT time, flow_value
                FROM flow_data
                WHERE station_id = '{self.stationId}'
                AND time BETWEEN '{self.startTime}' AND '{self.endTime}'
                ORDER BY time
                """

        try:
            data = self.db_utils.query(sql)
            data = pd.DataFrame(data)
            data.columns = ['Time', 'FlowValue']
            self.data = data
            self.data['Time'] = pd.to_datetime(self.data['Time'])
        except Exception as e:
            raise APIException(msg="数据库连接异常!")

        print("这场洪水从数据库中获取的数据是：")
        print(self.data)

        # csv_file_path = 'D:\postgraduate\project\PatternLibrary\data/response.csv'
        # self.data = pd.read_csv(csv_file_path, header=0, names=['Time', 'FlowValue'])
        # print("csv文件里的数据是")
        # print(self.data)
        # self.data = pd.DataFrame(self.data)
        # 转换'Time'列为datetime类型
        # self.data['Time'] = pd.to_datetime(self.data['Time'])
        # 过滤出在开始时间和结束时间之间的数据
        # self.data = self.data[(self.data['Time'] >= self.startTime) & (self.data['Time'] <= self.endTime)]
        # print('过滤后的数据是：')
        # print(self.data)
        # 将 'Time' 列转换为列表
        self.timeList = self.data['Time'].tolist()
        # 将 'FlowValue' 列转换为列表
        self.flowList = self.data['FlowValue'].tolist()

    def get_PEAK_PATTERN(self):  # 获取峰值模式：peakPattern

        flow_length = len(self.flowList)
        if flow_length < 51:
            window_length = flow_length
            if flow_length % 2 == 0:
                window_length = flow_length + 1
        else:
            window_length = 51

        y_smooth = signal.savgol_filter(self.flowList, window_length, 3)
        # height：低于height的信号都不考虑，distance相邻峰之间的最小水平距离
        # peaks2 = signal.find_peaks(y_smooth, height=100, distance=72)
        peaks2 = signal.find_peaks(y_smooth, height=int(max(y_smooth) / 2), distance=72)
        if len(peaks2[1]['peak_heights']) == 0:
            self.peakPattern = "空"
        elif len(peaks2[1]['peak_heights']) == 1:
            self.peakPattern = "单峰"
        elif len(peaks2[1]['peak_heights']) == 2:
            self.peakPattern = "双峰"
        elif len(peaks2[1]['peak_heights']) > 2:
            self.peakPattern = "多峰"

        return self.peakPattern

    def get_DURATION_FLOOD(self):  # 计算持续时间：durationFlood

        start_Time = datetime.strptime(self.startTime, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(self.endTime, '%Y-%m-%d %H:%M:%S')
        time_difference = (end_time - start_Time).total_seconds() / 3600  # 计算时间差
        self.durationFlood = int(time_difference)

        return self.durationFlood

    def get_PEAK_FLOOD(self):  # 计算流量峰值：peakFlood

        max_float = -1
        b = [float(i) for i in self.flowList]
        for i in b:
            if max_float < i:
                max_float = i
        if max_float != -1:
            self.peakFlood = max_float

        return self.peakFlood

    def get_PEAK_FLOOD_TIME(self):  # 计算最大流量时间： peakFloodTime

        max_index = self.flowList.index(max(self.flowList))
        self.peakFloodTime = self.timeList[max_index]

        return self.peakFloodTime

    def get_TOTAL_FLOOD(self):  # 获取洪水总量：totalFlood

        self.totalFlood = round(sum(self.flowList), 2)

        return self.totalFlood

    def get_START_LAST_TIME(self):  # 计算洪水开始多久到达峰值（小时）： startLastTime

        max_index = self.flowList.index(max(self.flowList))
        self.startLastTime = max_index

        return self.startLastTime

    def get_END_LAST_TIME(self):  # 计算洪水到达峰值后持续多久（小时）：endLastTime

        max_index = self.flowList.index(max(self.flowList))
        self.endLastTime = len(self.flowList) - max_index - 1

        return self.endLastTime

    def save_FEATURE_2_DB(self):
        if self.resultState == {}:
            raise APIException("特征值计算有误!")
        #对flood_feature表的保存
        sql = ("INSERT INTO flood_feature (flood_id, peak_pattern, peak_time, peak_flow, start_time, "
               "end_time, time_to_peak, dur_time, flood_flow_sequence, total_flow) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s ,%s)")
        # 对flood_time_data表的保存
        save_time_data_sql = '''
            INSERT INTO flood_time_data (flood_id, time, flow_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                flow_value = VALUES(flow_value)
        '''
        try:
            # 对flood_feature表的保存
            flood_id = self.floodId
            peak_pattern = self.peakPattern
            peak_time = self.peakFloodTime
            peak_flow = self.peakFlood
            start_time = self.startTime
            end_time = self.endTime
            time_to_peak = self.startLastTime
            dur_time = self.durationFlood
            # flood_flow_sequence = self.flowList
            flood_flow_sequence = json.dumps(self.flowList)  # 转换为 JSON 字符串
            total_flow = self.totalFlood

            feature_data = (flood_id, peak_pattern, peak_time, peak_flow, start_time, end_time, time_to_peak, dur_time, flood_flow_sequence, total_flow)
            feature_id = self.db_utils.insert_and_getId(sql, feature_data)

            # 对flood_time_data表的保存
            if self.resultState['FLOW_FLOOD_STATE'] == 1:
                for i in range(len(self.timeList)):
                    self.db_utils.exec(save_time_data_sql, (self.floodId, self.timeList[i], self.flowList[i]))

            return feature_id

        except Exception as e:
            ######错误信息报can only concatenate str (not "DatabaseError") to str时使用下面代码
            e = str(e).replace('"', '*')
            e = e.replace("'", '*')
            print("更新数据时出错: ", e)
            return None

        finally:
            self.db_utils.__del__()



    def get_FlowFeature(self):

        self.get_PEAK_PATTERN()
        self.get_DURATION_FLOOD()
        self.get_PEAK_FLOOD()
        self.get_PEAK_FLOOD_TIME()
        self.get_TOTAL_FLOOD()
        self.get_START_LAST_TIME()
        self.get_END_LAST_TIME()

        print("特征值分别为：")
        print("峰值模式：{}".format(self.peakPattern)+"\n洪水持续时间：{}".format(self.durationFlood)+"\n流量峰值：{}".format(self.peakFlood)+"\n峰值时间：{}".format(self.peakFloodTime)+"\n"+
              "流量总量:{}".format(self.totalFlood)+"\n开始多久到峰值：{}".format(self.startLastTime)+"\n结束时间:{}".format(self.endLastTime)+"\n洪水序列:{}".format(self.flowList))
        # print(self.totalFlood,self.startLastTime,self.endLastTime,self.flowList)
        # 收集特征提取状态
        resultState = {}
        resultState['FLOOD_ID'] = self.floodId
        resultState['PEAK_PATTERN'] = 0 if self.peakPattern is None else 1
        resultState['DURATION_FLOOD'] = 0 if self.durationFlood is None else 1
        resultState['PEAK_FLOOD'] = 0 if self.peakFlood is None else 1
        resultState['PEAK_FLOOD_TIME'] = 0 if self.peakFloodTime is None else 1
        resultState['TOTAL_FLOOD'] = 0 if self.totalFlood is None else 1
        resultState['START_LAST_TIME'] = 0 if self.startLastTime is None else 1
        resultState['END_LAST_TIME'] = 0 if self.endLastTime is None else 1
        resultState['FLOW_FLOOD_STATE'] = 0 if None in self.flowList or len(self.flowList) != len(
            self.timeList) else 1
        print('流量特征提取结果')
        print(resultState)
        self.resultState = resultState

        self.save_FEATURE_2_DB()

        return self.resultState

