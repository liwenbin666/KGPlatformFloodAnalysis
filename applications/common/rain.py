from datetime import datetime, timedelta
import re
import numpy
import pandas as pd
from geopy.distance import distance
import numpy as np
import ast
import os
from applications.common.utils.database import DBUtils
from scipy import signal


class Rain():
    def __init__(self, floodId, stationId, startTime, endTime):

        self.floodId = floodId
        self.basinId = None
        self.stationId = stationId
        self.startTime = startTime
        self.endTime = endTime

        # 数据库操作工具
        self.db_utils = DBUtils()

        self.data = None
        self.stations = None
        self.rainData = None
        self.rainList = None
        self.flowList = None
        self.StageList = None
        self.timeList = None
        self.resultState = {}
        self.minLon = None
        self.maxLon = None
        self.minLat = None
        self.maxLat = None
        # 面雨量相关特征
        self.rows = None  # 网格分为多少行
        self.cols = None  # 网格分为多少列
        self.gridRainDf = None  # 网格雨量序列
        self.rainMax = None
        self.maxIndex = None
        self.rainCenter = None
        self.rainCenterSide = None
        self.arealRain = None
        self.rainSum = None
        self.maxGridRainfall = None
        self.rainTrend = None
        self.gridRainfall = None
        self.dataPrePath = None  # 根据工作目录定位不同的相对路径

        # 在station表中读取所在流域id
        basin_sql = f"""
                SELECT basin_id
                FROM station
                WHERE id >= %s
                AND station_type = 0
                """

        # 在station和rain_data表里读取该洪水发生所在流域的雨量数据
        rainData_sql = f"""
                        SELECT time, station_id, rain_value
                        FROM rain_data
                        WHERE station_id IN (
                            SELECT id
                            FROM station
                            WHERE basin_id = %s
                            AND station_type = 1
                        ) AND time >= %s AND time <= %s
                        ORDER BY time, station_id
                        """

        # 在basin表读取流域的经纬度范围
        lon_lat_sql = f"""
                SELECT longitude_range, latitude_range
                FROM basin
                where id = %s
                """

        try:

            # 获取流域ID
            # self.data = self.db_utils.query(basin_sql, (self.stationId))
            # self.basinId = self.data[0][0]  # 提取元组中的第一个元素作为流域id
            try:
                self.data = self.db_utils.query(basin_sql, (self.stationId,))
                # print("从数据库中获取的流域信息是:")
                # print(self.data)
                # 提取元组中的第一个元素作为流域id
                # self.basinId = self.data[0][0]
                self.basinId = self.data[0]['basin_id']
                print("流域ID")
                print(self.basinId)
            except Exception as e:
                print("查询数据时出错: ", e)
            # print(self.basinId)
            ##########################

            self.data = self.db_utils.query(rainData_sql, (self.basinId, self.startTime, self.endTime))
            # print("原始雨量数据:")
            # print(self.data)

            # 获取唯一的时间戳和测站ID
            timestamps = sorted(list(set(row['time'] for row in self.data)))
            self.stations = sorted(list(set(row['station_id'] for row in self.data)))
            self.timeList = timestamps

            # 创建行数与时间戳相同、列数与测站ID相同的二维数组
            self.rainData = [[None] * len(self.stations) for _ in timestamps]

            # 创建时间戳和测站ID到其索引的映射
            timestamp_to_index = {timestamp: index for index, timestamp in enumerate(timestamps)}
            station_id_to_index = {station_id: index for index, station_id in enumerate(self.stations)}

            # 用测量值填充数组
            for row in self.data:
                time_index = timestamp_to_index[row['time']]
                station_index = station_id_to_index[row['station_id']]
                self.rainData[time_index][station_index] = row['rain_value']

            print("填充后的雨量数据是:")
            print(self.rainData)


            # 每小时各个测站的平均值作为改时间雨量列表中的值
            self.rainList = []
            for row in self.rainData:
                # self.rainList.append(round(numpy.average(row), 2))
                self.rainList = [round(np.nanmean(row), 2) for row in self.rainData]  # 使用 nanmean 以防 None 值
                # print(row)
            # print(self.rainList)

            ## 获取流域的经纬度范围
            self.data = self.db_utils.query(lon_lat_sql, self.basinId)
            print("经纬度范围是:")
            # print(self.data)
            strLONGITUDE_RANGE = self.data[0]['longitude_range']

            # print(type(strLONGITUDE_RANGE))
            LONGITUDE_RANGE = ast.literal_eval(strLONGITUDE_RANGE)  # 从字符串中提取经度范围
            self.minLon = LONGITUDE_RANGE[0]
            self.maxLon = LONGITUDE_RANGE[1]
            strLATITUDE_RANGE = self.data[0]['latitude_range']
            LATITUDE_RANGE = ast.literal_eval(strLATITUDE_RANGE)  # 从字符串中提取经度范围
            self.minLat = LATITUDE_RANGE[0]
            self.maxLat = LATITUDE_RANGE[1]

            print("经度范围:", self.minLon, self.maxLon)
            print("纬度范围:", self.minLat, self.maxLat)
            #########################

            # self.db_utils.__del__()

            # 修正工作目录
            current_directory = os.getcwd()
            print('dir', current_directory)
            self.dataPrePath = os.getcwd()
            if 'common' in current_directory:
                print('本地测试')
                self.dataPrePath = os.path.join(self.dataPrePath, '../../')
            else:
                print('使用接口')
                self.dataPrePath = current_directory
                print('dataPrePath', self.dataPrePath)
        except Exception as e:
            print("查询数据时出错: ", e)

    @staticmethod
    # 将度分秒的经纬度转为小数点形式
    def dms_to_degree(dms_str):
        """
        将度分秒（DMS）格式的字符串转换为十进制度数。

        参数:
        dms_str (str): 表示度分秒的字符串，例如 "123°34′56″"

        返回:
        float: 对应的十进制度数，如果输入格式不正确，则返回 None
        """
        # 匹配度分秒的正则表达式
        pattern = r'(\d+)°(\d+)′(\d+)″'
        match = re.match(pattern, dms_str)
        if match:
            # 分别取出度、分、秒
            degree = int(match.group(1))
            minute = int(match.group(2))
            second = int(match.group(3))
            # 计算出十进制度数
            return degree + minute / 60 + second / 3600
        else:
            return None

    def get_targetID(self):
        # 经纬度范围
        # lat1, lat2 = self.minLat, self.maxLat
        lat1 = self.minLat
        lat2 = self.maxLat
        lon1, lon2 = self.minLon, self.maxLon

        print(f"lat1: {lat1}, lat2: {lat2}")

        # 计算两点距离
        dist = distance((lat1, lon1), (lat2, lon2)).km  # 两点距离
        xdist = (lat2 - lat1) * 111  # 垂直距离，111 km approximately equals 1 degree of latitude
        ydist = np.sqrt(dist ** 2 - xdist ** 2)  # 水平距离

        # 计算行列数
        grid_size = 1  # 1平方千米的网格大小
        num_rows = int(np.ceil(xdist / grid_size))
        num_cols = int(np.ceil(ydist / grid_size))
        self.cols = num_cols

        # 计算起点
        start_lat, start_lon = lat1, lon1

        # 计算每个网格的中心点坐标
        centers = []
        for i in range(num_rows):
            row_centers = []
            for j in range(num_cols):
                # 计算中心点坐标
                center_lat = start_lat + (i + 0.5) * (lat2 - lat1) / num_rows
                center_lon = start_lon + (j + 0.5) * (lon2 - lon1) / num_cols
                row_centers.append((center_lat, center_lon))
            centers.append(row_centers)

        # 创建 DataFrame
        data = {
            '区站号': [],
            '东经': [],
            '北纬': []
        }
        for i, row in enumerate(centers):
            for j, (lat, lon) in enumerate(row):
                data['区站号'].append(i * num_cols + j + 1)
                data['东经'].append(lon)
                data['北纬'].append(lat)

        df = pd.DataFrame(data)

        # 输出结果到文件
        result_filename = os.path.join(self.dataPrePath, 'static/datas/areadata/targetID.txt')
        df.to_csv(result_filename, sep=',', index=False)

    def get_ObsID(self):
        # 生成流域中雨量站的经纬度信息
        # 从station表里读取洪水所在流域的雨量站信息
        station_sql = '''
            SELECT id, longitude, latitude
            FROM station 
            WHERE basin_id = %s
            AND station_type = 1
        '''

        # 初始化 DataFrame
        df = pd.DataFrame(columns=['区站号', '东经', '北纬'])
        try:
            self.data = self.db_utils.query(station_sql, self.basinId)
            print("原始测站信息查询结果：", self.data)  # 调试信息

            # 用查询结果填充 DataFrame
            if self.data:
                data = [{"区站号": row['id'], "东经": row['longitude'], "北纬": row['latitude']} for row in self.data]
                df = pd.DataFrame(data)
                print("生成的测站DataFrame：\n", df)  # 调试信息


            # 关闭数据库连接
            # self.db_utils.__del__()
        except Exception as e:
            print("查询数据时出错：", e)
            # self.db_utils.__del__()  # 确保异常情况下也关闭连接

        # 输出结果到文件
        result_filename = os.path.join(self.dataPrePath, 'static/datas/areadata/ObsID.txt')
        df.to_csv(result_filename, sep=',', index=False)
        print(f"结果写入文件：{result_filename}")  # 调试信息

    def get_Precipitation(self):
        # 获取现有雨量站雨量信息
        df = pd.DataFrame(self.rainData, columns=self.stations)
        result_filename = os.path.join(self.dataPrePath, 'static/datas/areadata/Precipitation.txt')
        df.to_csv(result_filename, sep=',', index=False)

    ###############################面雨量特征计算############################################
    def get_Dataframe(self):
        # 读取插值后的网格数据
        filename = os.path.join(self.dataPrePath, 'static/datas/areadata/res.txt')
        df = pd.read_csv(filename, header=None)
        # 将值为-99.0的元素替换为0
        df = df.replace(-99.0, 0)
        self.rows = df.shape[0]
        self.cols = df.shape[1]

        self.gridRainDf = df

    def Decrease_1hour(self, Timestr):
        # 返回时间字符串减少一小时的结果
        Timestr = datetime.strptime(Timestr, "%Y%m%d%H")
        Time = Timestr - timedelta(hours=1)
        Decrease_Time = datetime.strftime(Time, "%Y%m%d%H")
        return Decrease_Time

    def Increase_1hour(self, Timestr):
        # 返回时间字符串增加一小时的结果
        Timestr = datetime.strptime(Timestr, "%Y%m%d%H")
        Time = Timestr + timedelta(hours=1)
        Increase_Time = datetime.strftime(Time, "%Y%m%d%H")
        return Increase_Time

    def out_coordinate(self, index, line):
        # 将索引转为坐标，line为将区域分为多少列
        x = int(index / line)
        y = index % line
        # print(x, y)
        coordinate = (x, y)
        return coordinate

    def add_element_to_tuple(self, tup, c):
        # 在元组tup的基础上追加添加c元素
        lst = list(tup)
        lst.append(int(c))
        new_tup = tuple(lst)
        return new_tup

    def add_element_to_doubletuple(self, tup, c):
        # 将一个浮点数添加到元组末尾，生成一个新的元组
        lst = list(tup)
        c = round(c, 1)
        lst.append(float(c))
        new_tup = tuple(lst)
        return new_tup

    def grid_to_latlon(self, x, y, start_lat, start_lon, lat_increment, lon_increment):
        """转换网格坐标到经纬度坐标"""
        new_lat = start_lat + x * lat_increment
        new_lon = start_lon + y * lon_increment
        return new_lat, new_lon

    def get_Rain_Max(self):
        # 计算RAIN_MAX, MAX_INDEX, RAIN_CENTER, RAIN_CENTER_SIDE
        Time = datetime.strptime(self.startTime, "%Y-%m-%d %H:%M:%S")
        startTime = datetime.strftime(Time, "%Y%m%d%H")
        rows = self.gridRainDf.shape[0]  # 行数
        cols = self.gridRainDf.shape[1]  # 列数

        FirstTime = self.Decrease_1hour(startTime)
        FirstTup = (0, 0, int(FirstTime))
        RAIN_MAX = []
        MAX_INDEX = []
        RAIN_CENTER = []
        RAIN_CENTER_SIDE = []

        for i in range(rows):
            # 更新时间
            if i == 0:
                startTime = self.Decrease_1hour(startTime)  # 只在第一次循环中减少时间

            # 计算rain_max, max_index
            max_value = self.gridRainDf.iloc[i].max()  # 最大降雨量
            column_index = self.gridRainDf.iloc[i][self.gridRainDf.iloc[i] == max_value].index[0]

            RAIN_MAX.append(max_value)
            MAX_INDEX.append(column_index)
            Coordinate = self.out_coordinate(column_index, self.cols)

            rain_center = self.add_element_to_tuple(Coordinate, startTime)
            RAIN_CENTER.append(str(rain_center))

            if i == 0:
                # 只在第一个元素添加前一个状态
                RAIN_CENTER_SIDE.append([str((0, 0, int(self.Decrease_1hour(startTime)))), str(rain_center)])
            else:
                RAIN_CENTER_SIDE.append([str(RAIN_CENTER[-2]), str(rain_center)])

            startTime = self.Increase_1hour(startTime)  # 确保在每次循环结束时增加时间


        self.rainMax = RAIN_MAX
        self.maxIndex = MAX_INDEX
        self.rainCenter = RAIN_CENTER
        self.rainCenterSide = RAIN_CENTER_SIDE

    def update_rain_coordinates(self):
        """更新雨中心和雨中心侧的经纬度坐标"""
        if self.rows is None or self.cols is None:
            raise ValueError("网格的行数和列数必须被正确设置")

        start_lat = self.minLat
        start_lon = self.minLon
        lat_increment = (self.maxLat - self.minLat) / self.rows
        lon_increment = (self.maxLon - self.minLon) / self.cols

        # 更新 rain_center 的坐标
        updated_rain_center = []
        for center in self.rainCenter:
            x, y, time = map(int, center.strip('()').split(', '))
            lat, lon = self.grid_to_latlon(x, y, start_lat, start_lon, lat_increment, lon_increment)
            updated_rain_center.append(f"({lat}, {lon}, {time})")
        self.rainCenter = updated_rain_center

        # 更新 rain_center_side 的坐标
        updated_rain_center_side = []
        for pair in self.rainCenterSide:
            updated_pair = []
            for center in pair:
                x, y, time = map(int, center.strip('()').split(', '))
                lat, lon = self.grid_to_latlon(x, y, start_lat, start_lon, lat_increment, lon_increment)
                updated_pair.append(f"({lat}, {lon}, {time})")
            updated_rain_center_side.append(updated_pair)
        self.rainCenterSide = updated_rain_center_side

    def get_Area_Rain(self):
        # 计算AREAL_RAIN , RAIN_SUM, MAX_GRID_RAINFALL
        df = self.gridRainDf
        AREAL_RAIN_LIST = df.sum(axis=1)  # 按行求和
        MAX_GRID_RAINFALL_LIST = df.sum(axis=0)  # 按列求和
        MAX_GRID_RAINFALL_VALUE = MAX_GRID_RAINFALL_LIST.max()
        MAX_GRID_RAINFALL_INDEX = MAX_GRID_RAINFALL_LIST.idxmax()
        MAX_GRID_RAINFALL_XY = self.out_coordinate(MAX_GRID_RAINFALL_INDEX, self.cols)
        MAX_GRID_RAINFALL = self.add_element_to_doubletuple(MAX_GRID_RAINFALL_XY, MAX_GRID_RAINFALL_VALUE)
        AREAL_RAIN = []
        for i in AREAL_RAIN_LIST:
            AREAL_RAIN.append(int(i))

        RAIN_SUM = sum(AREAL_RAIN)

        self.arealRain = AREAL_RAIN
        self.rainSum = RAIN_SUM
        self.maxGridRainfall = MAX_GRID_RAINFALL

    def get_Rain_Trend(self):
        # 计算RAIN_TREND
        df = self.gridRainDf
        row_means = df.mean(axis=1)  # 行均值
        rows = df.shape[0]  # 行数
        cols = df.shape[1]  # 列数
        RAIN_TREND = []

        for i in range(rows):
            squared_diffs = (df.iloc[i] - row_means[i]) ** 2
            trend_point = squared_diffs.mean()
            RAIN_TREND_POINT = round(trend_point, 4)
            RAIN_TREND.append(RAIN_TREND_POINT)

        self.rainTrend = RAIN_TREND

    def get_Grid_Rainfall(self):

        df = self.gridRainDf
        GRID_RAINFALL_LIST = df.sum(axis=0).astype(int).tolist()  # 按列求和并转换为整数列表

        self.gridRainfall = GRID_RAINFALL_LIST

    def save_Rain_Feature(self):
        print("特征值保存中")
        # 对rain_feature表的保存
        save_rain_feature_sql = '''
                INSERT INTO rain_feature (
                    flood_id, rain_sum, rainfall_state,
                    rain_max_state, rain_trend_state,
                    areal_rain_state, rain_center_state, rain_center_side_state,
                    max_index_state, grid_rainfall_path, max_grid_rainfall
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

        # 对flood_time_data表的更新
        update_time_data_sql = '''
        UPDATE flood_time_data
        SET 
            rainfall_value = %s,
            rain_max = %s,
            rain_trend = %s,
            areal_rain = %s,
            rain_center = %s,
            rain_center_side = %s,
            max_index = %s
        WHERE time = %s;
        '''

        try:
            # 对于rain_feature表
            self.data = self.db_utils.exec(save_rain_feature_sql, (
                self.floodId, int(self.rainSum), self.resultState['RAINFALL_STATE'],
                self.resultState['RAIN_MAX_STATE'], self.resultState['RAIN_TREND_STATE'],
                self.resultState['AREAL_RAIN_STATE'], self.resultState['RAIN_CENTER_STATE'],
                self.resultState['RAIN_CENTER_SIDE_STATE'], self.resultState['MAX_INDEX_STATE'],
                self.resultState['GRID_RAINFALL_STATE'], str(self.maxGridRainfall)
            ))

            # 对于flood_time_data表
            for i in range(len(self.timeList)):
                rainList = None if self.rainList is None else self.rainList[i]
                rainMax = None if self.rainMax is None else self.rainMax[i]
                rainTrend = None if self.rainTrend is None else self.rainTrend[i]
                arealRain = None if self.arealRain is None else self.arealRain[i]
                rainCenter = None if self.rainCenter is None else self.rainCenter[i]
                rainCenterSide = None if self.rainCenterSide is None else self.rainCenterSide[i]
                maxIndex = None if self.maxIndex is None else self.maxIndex[i]
                timeValue = self.timeList[i]

                # 打印调试信息
                print(f"Updating record for time: {timeValue}")
                print(f"rainList: {rainList}, rainMax: {rainMax}, rainTrend: {rainTrend}, arealRain: {arealRain}")
                print(f"rainCenter: {rainCenter}, rainCenterSide: {rainCenterSide}, maxIndex: {maxIndex}")

                # 确保参数是单一值且格式正确
                if isinstance(rainCenter, tuple):
                    rainCenter = ', '.join(map(str, rainCenter))
                if isinstance(rainCenterSide, list):
                    rainCenterSide = ', '.join(rainCenterSide)
                if not isinstance(timeValue, str):
                    timeValue = timeValue.strftime('%Y-%m-%d %H:%M:%S')

                params = (rainList, rainMax, rainTrend, arealRain,
                          rainCenter, rainCenterSide, maxIndex, timeValue)

                self.db_utils.exec(update_time_data_sql, params)

            # self.db_utils.__del__()

        except Exception as e:
            import traceback
            error_message = str(e).replace('"', '*').replace("'", '*')
            traceback_message = traceback.format_exc().replace('"', '*').replace("'", '*')
            print(f"更新数据时出错: {error_message}")
            print(f"堆栈信息: {traceback_message}")

    def get_Rain_Feature(self):

        # 计算面雨量需要的数据
        print("计算网格雨量准备文件")
        self.get_targetID()
        self.get_ObsID()
        self.get_Precipitation()

        JavaPath = os.path.join(self.dataPrePath, 'static', 'jar', 'idw.jar')
        run_jar(JavaPath)  # 执行jar包获取面雨量数据

        print("开始计算特征值")
        self.get_Dataframe()
        self.get_Area_Rain()
        self.get_Rain_Max()
        self.get_Rain_Trend()
        self.get_Grid_Rainfall()
        self.update_rain_coordinates()
        print("rain_center:")
        print(self.rainCenter)
        print("Length of self.rainCenter:", len(self.rainCenter))
        print("Length of self.rainCenterSide:", len(self.rainCenterSide))
        print("Length of self.timeList:", len(self.timeList))

        # 收集特征值提取状态
        result_state = {}
        result_state['RAINFALL_STATE'] = 0 if None in self.rainList or len(self.rainList) != len(self.timeList) else 1
        result_state['RAIN_SUM'] = 0 if self.rainSum is None else 1
        result_state['RAIN_MAX_STATE'] = 0 if None in self.rainMax or len(self.rainMax) != len(self.timeList) else 1
        result_state['RAIN_TREND_STATE'] = 0 if None in self.rainTrend or len(self.rainTrend) != len(
            self.timeList) else 1
        result_state['AREAL_RAIN_STATE'] = 0 if None in self.arealRain or len(self.arealRain) != len(
            self.timeList) else 1
        result_state['RAIN_CENTER_STATE'] = 0 if None in self.rainCenter or len(self.rainCenter) != len(
            self.timeList) else 1
        result_state['RAIN_CENTER_SIDE_STATE'] = 0 if None in self.rainCenterSide or len(self.rainCenterSide) != len(
            self.timeList) else 1
        result_state['MAX_INDEX_STATE'] = 0 if None in self.maxIndex or len(self.maxIndex) != len(self.timeList) else 1
        result_state['GRID_RAINFALL_STATE'] = 0 if self.gridRainfall is None else 1
        result_state['MAX_GRID_RAINFALL'] = 0 if self.maxGridRainfall is None else 1

        if result_state['GRID_RAINFALL_STATE'] == 1:  # 保存GRID_RAINFALL至本地
            array = np.array(self.gridRainfall)
            # 将数组转换为 pandas 的 DataFrame 对象
            df = pd.DataFrame(array.reshape(-1, self.cols))  # 分割为二维数组
            # 将 DataFrame 对象写入txt 文件
            datapath = os.path.join(self.dataPrePath, 'static', 'datas', 'gridrainfalldata', f'{self.floodId}.txt')
            df.to_csv(datapath, index=False, header=False)

        print('降水特征提取结果')
        print(result_state)
        # print(len(self.GRID_RAINFALL))
        self.resultState = result_state

        self.save_Rain_Feature()

        self.db_utils.__del__()
        ##################################################################
        return result_state


import subprocess


def run_jar(jar_path):
    command = ['java', '-jar', jar_path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Error occurred: {error}")
    else:
        print(f"Output: {output}")