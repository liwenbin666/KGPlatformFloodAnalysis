import pandas as pd
import scipy.signal as signal
from applications.exception.my_exception import APIException
import datetime
from applications.common.utils.database import DBUtils
from applications.common.utils.resample import resample_time_series
from applications.common.utils.http_status_codes import HTTPStatusCodes


class SliceFlood():

    def __init__(self, stationId, startTime, endTime, height, distance, duration):

        self.stationId = stationId
        self.basinId = None
        self.basinArea = None
        self.startTime = startTime
        self.endTime = endTime
        self.height = height
        self.distance = distance
        self.duration = duration
        self.data = None
        self.slice_res = None
        self.flood_times = []  # 用于存储已划分的场次时间范围
        self.db_utils = DBUtils()

        # SQL查询
        sql = f"""
        SELECT time, flow_value
        FROM gen_flow_data
        WHERE station_id = '{self.stationId}'
        AND time BETWEEN '{self.startTime}' AND '{self.endTime}'
        ORDER BY time
        """

        try:
            data = self.db_utils.query(sql)
            data = pd.DataFrame(data)
            data.columns = ['Time', 'FlowValue']
            # print("数据库中获取的数据是：")
            # print(data)
            # 使用重采样函数
            self.data = resample_time_series(data, index_column='Time', sample_rate='h', fill_method='spline', order=3)
            # print("resample_time_series后的数据")
            # print(self.data)
            # self.data = data
            # self.data['Time'] = pd.to_datetime(self.data['Time'])
        except Exception as e:
            raise APIException(msg="数据库连接异常!",code=HTTPStatusCodes.SERVICE_UNAVAILABLE)

        flood_times_sql = "SELECT start_time, end_time, peak_time FROM gen_flood_events WHERE station_id = %s"
        flood_event = self.db_utils.query(flood_times_sql, (self.stationId,))
        # print("数据库中获取洪水事件的数据是：")
        # print(self.data)
        if flood_event:
            for row in flood_event:
                self.flood_times.append({
                    "start_date": row['start_time'],
                    "end_date": row['end_time'],
                    "peak_date": row['peak_time']
                })

    def find_peak(self):
        flow = self.data['FlowValue'].tolist()
        flow_length = len(flow)
        if flow_length < 41:
            window_length = flow_length
            if flow_length % 2 == 0:
                window_length = flow_length + 1
        else:
            window_length = 41

        flow_smooth = signal.savgol_filter(flow, window_length, 4)
        peaks = signal.find_peaks(flow_smooth, height=self.height, distance=self.distance)
        if len(peaks[0]) == 0:
            raise APIException(msg="当前配置无法划分场次,请重新输入和划分相关的参数!",code=HTTPStatusCodes.SERVICE_UNAVAILABLE)

        print(peaks)
        return peaks[0]

    def slice_according_time_range(self, peak):
        '''
        根据峰值时间前后推场次
        :param peak: 峰值数组
        :param time_range: 时间跨度,day为单位
        :return:
        '''
        slice_res = {}
        data = self.data
        left_date = data.loc[0]['Time']
        right_date = data.loc[data.shape[0] - 1]['Time']
        for p in peak:
            peak_time = data.loc[p]['Time']
            start_time = peak_time - datetime.timedelta(days=self.duration / 2)
            end_time = peak_time + datetime.timedelta(days=self.duration / 2)
            is_overlap = False

            for flood_time in self.flood_times:
                if start_time < flood_time['end_date'] and end_time > flood_time['start_date']:
                    is_overlap = True
                    break

            if is_overlap:
                continue

            # # 检查时间重叠并进行调整
            # for flood_time in self.flood_times:
            #     if start_time < flood_time['end_date'] and end_time > flood_time['start_date']:
            #         # 如果有重叠，调整开始或结束时间
            #         if start_time < flood_time['start_date']:
            #             end_time = min(end_time, flood_time['start_date'])
            #         else:
            #             start_time = max(start_time, flood_time['end_date'])
            if start_time < left_date:  # 防止超出边界
                start_time = left_date
            if end_time > right_date:
                end_time = right_date
            slice_res[p] = {
                "start_date": start_time,
                "end_date": end_time,
                "peak_date": peak_time
            }
        self.slice_res = slice_res
        # print('划分结果:{}'.format(slice_res))
        return slice_res

    def save_res_2_db(self):
        if self.slice_res is None:
            raise APIException(msg="划分场次出错，场次结果为0", code=HTTPStatusCodes.INTERNAL_SERVER_ERROR)
        if len(self.slice_res) == 0:
            raise APIException(msg="划分场次出错，场次结果存在重叠",code=HTTPStatusCodes.FORBIDDEN)

        flood_ids = []
        sql = "INSERT INTO gen_flood_events (station_id, start_time, end_time, peak_time) VALUES (%s, %s, %s, %s)"
        for key, value in self.slice_res.items():
            station_id = self.stationId
            start_date = value['start_date']
            end_date = value['end_date']
            peak_date = value['peak_date']

            flood_event = (station_id, start_date, end_date, peak_date)
            flood_id = self.db_utils.insert_and_getId(sql, flood_event)
            if flood_id:
                flood_ids.append(flood_id)

        return flood_ids

    def slice_flood(self):
        peaks = self.find_peak()
        slice_res = self.slice_according_time_range(peaks)
        flood_ids = self.save_res_2_db()
        print("场次ID集合：{}".format(flood_ids))

        # 创建一个新的字典来存储带有 flood_id 的 slice_res
        new_slice_res = {}

        # 确保 flood_ids 的长度与 slice_res 中的键数量相同
        if len(flood_ids) != len(slice_res):
            raise ValueError("flood_ids 列表的长度必须与 slice_res 中的键数量相同")

        # 遍历 slice_res 中的条目，并插入对应的 flood_id
        for (key, timestamps), flood_id in zip(slice_res.items(), flood_ids):
            # 将 flood_id 添加到 timestamps 字典中
            new_entry = timestamps.copy()
            new_entry['flood_id'] = flood_id
            # 将更新后的字典添加到 new_slice_res 中
            new_slice_res[key] = new_entry

        print("新的划分结果是：{}".format(new_slice_res))

        # try:
        #     self.save_res_2_db()
        # except Exception as e:
        #     raise APIException("场次划分出错！")

        return new_slice_res
