import json
import numpy as np
import pandas as pd
from datetime import datetime
from applications.common.utils.database import DBUtils
from applications.configuration.JsonConfig import NpEncoder
from applications.common.utils.http_status_codes import HTTPStatusCodes
from applications.exception.my_exception import APIException
from dtw import dtw
import logging

class MdtwMatch():
    def __init__(self, floodId, weights):
        self.id = floodId
        # print("当前ID",self.id)
        self.res_id = None
        self.res_3_id = None
        self.weights = weights
        self.columns = ['FLOOD_ID', 'RAINFALL_VALUE', 'RAIN_TREND', 'AREAL_RAIN', 'MAX_INDEX',
                        'RAIN_SUM', 'GRID_RAIN_MAX', 'MAX_GRID_RAINFALL', 'FLOW_VALUE', 'PEAK_FLOOD', 'TOTAL_FLOOD']
        conn = DBUtils()
        # 查询流量特征是否存在
        flow_feature_sql = f"""
                                    SELECT *
                                    FROM kb_flood_flow_feature
                                    WHERE flood_id = '{self.id}'
                        """
        flow_feature_data = conn.query(flow_feature_sql)
        # print("数据库中获取的数据是：")
        # print(flow_feature_data)
        # 查询降雨特征是否存在
        rain_feature_sql = f"""
                                            SELECT *
                                            FROM kb_flood_rain_feature
                                            WHERE flood_id = '{self.id}'
                                """
        rain_feature_data = conn.query(rain_feature_sql)
        # print("数据库中获取的数据是：")
        # print(rain_feature_data)
        if flow_feature_data is None or rain_feature_data is None:
            raise APIException(msg="请先进行特征提取再匹配！", code=HTTPStatusCodes.SERVICE_UNAVAILABLE)

        all_ids_sql = "select flood_id from kb_flood_time_data group by flood_id;"

        sql = """
                SELECT 
                    a.flood_id, 
                    a.peak_flow, 
                    a.total_flow, 
                    b.max_grid_rainfall, 
                    b.rain_sum 
                FROM 
                    kb_flood_flow_feature a
                INNER JOIN 
                    kb_flood_rain_feature b 
                ON 
                    a.flood_id = b.flood_id;
                """

        try:
            conn = DBUtils()
            ids = conn.query(all_ids_sql)
            logging.debug(f"Raw ids query result: {ids}")
            if not ids:
                logging.error("No flood IDs found in the database.")
                raise ValueError("No flood IDs found in the database.")

            if not all(isinstance(x, dict) and 'flood_id' in x for x in ids):
                logging.error(f"Incorrect format of ids: {ids}")
                raise ValueError("Incorrect format of ids from database query.")

            ids = [x['flood_id'] for x in ids]
            logging.debug(f"Processed ids: {ids}")
            if not ids:
                logging.error("No valid flood IDs found after processing.")
                raise ValueError("No valid flood IDs found after processing.")

            data = conn.query(sql)
            # print("数据库中返回的data")
            # print(data)
            logging.debug(f"Raw data query result: {data}")
            if not data:
                logging.error("No data found in the database.")
                raise ValueError("No data found in the database.")

            data = pd.DataFrame(data)
            # print("处理后的data")
            # print(data)
            data.columns = ['FLOOD_ID', 'PEAK_FLOOD', 'TOTAL_FLOOD', 'MAX_GRID_RAINFALL', 'RAIN_SUM']
            # 为每行创建独立的空列表
            # for col in ['TIME', 'RAINFALL_VALUE', 'RAIN_TREND', 'AREAL_RAIN', 'MAX_INDEX', 'RAIN_MAX', 'FLOW_VALUE']:
            #     data[col] = data.apply(lambda x: [], axis=1)
            data['TIME'] = [[]] * data.shape[0]
            data['RAINFALL_VALUE'] = [[]] * data.shape[0]
            data['RAIN_TREND'] = [[]] * data.shape[0]
            data['AREAL_RAIN'] = [[]] * data.shape[0]
            data['MAX_INDEX'] = [[]] * data.shape[0]
            data['GRID_RAIN_MAX'] = [[]] * data.shape[0]
            data['FLOW_VALUE'] = [[]] * data.shape[0]

            # print("ids", ids)


            for id in ids:
                sql1 = f"select flood_id, time, rainfall_value, rain_trend, areal_rain, max_index, grid_rain_max, flow_value from kb_flood_time_data where flood_id = {id} order by time;"
                time_data = conn.query(sql1)
                if not time_data:
                    logging.warning(f"No time data found for flood ID {id}.")
                    continue
                time_data = pd.DataFrame(time_data)
                if time_data.empty:
                    logging.warning(f"No time data returned for flood ID {id}.")
                    continue
                time_data.columns = ['FLOOD_ID', 'TIME', 'RAINFALL_VALUE', 'RAIN_TREND', 'AREAL_RAIN', 'MAX_INDEX',
                                     'GRID_RAIN_MAX', 'FLOW_VALUE']
                row_indices = data.loc[data['FLOOD_ID'] == id].index
                if row_indices.empty:
                    logging.warning(f"No matching row found for flood ID {id}.")
                    continue
                row_number = row_indices[0]

                data.at[row_number, 'TIME'] = time_data['TIME'].values.tolist()
                data.at[row_number, 'RAINFALL_VALUE'] = time_data['RAINFALL_VALUE'].values.tolist()
                data.at[row_number, 'RAIN_TREND'] = time_data['RAIN_TREND'].values.tolist()
                data.at[row_number, 'AREAL_RAIN'] = time_data['AREAL_RAIN'].values.tolist()
                data.at[row_number, 'MAX_INDEX'] = time_data['MAX_INDEX'].values.tolist()
                data.at[row_number, 'GRID_RAIN_MAX'] = time_data['GRID_RAIN_MAX'].values.tolist()
                data.at[row_number, 'FLOW_VALUE'] = time_data['FLOW_VALUE'].values.tolist()

            self.data = data[
                ['FLOOD_ID', 'RAINFALL_VALUE', 'RAIN_TREND', 'AREAL_RAIN', 'MAX_INDEX', 'RAIN_SUM', 'GRID_RAIN_MAX',
                 'MAX_GRID_RAINFALL', 'FLOW_VALUE', 'PEAK_FLOOD', 'TOTAL_FLOOD']]
            # print("self.data:")
            # print(self.data)

            logging.debug(f"self.data: {self.data}")
            self.data = self.data[self.data['RAIN_SUM'] != 0]
            self.data = self.data.reset_index(drop=True)
            if self.data.empty:
                logging.error("Data is empty after initialization.")
                raise ValueError("Data is empty after initialization.")

            self.get_max_grid_rainfall_value()

        except Exception as e:
            logging.error("MDTW查询数据时出错: %s", e)
            raise e

    def get_max_grid_rainfall_value(self):
        values = [float(x.split(',')[2].split(')')[0]) for x in self.data['MAX_GRID_RAINFALL'] if isinstance(x, str)]
        for i in range(len(values)):
            self.data.loc[i,'MAX_GRID_RAINFALL'] = values[i]

    '''
        将数据转为一维矩阵?
        把数据库里的数据重整型为[10,n]的矩阵，然后把矩阵全放进mat_list中
        一个[10,n]的矩阵表示一场洪水，这里的10表示的是特征数，这里的n表示的是该场洪水的长度，比如一场洪水有269个记录值，那么这个矩阵就是[10,269]/
        至于说这个10也是可以变的，看你输入多少个特征把。
        如果不是时序数据，像max_index这种只有一个值的，那就前面填充n-1个0，最后一个数为max_index
    '''
    def get_mat_list(self):
        mat_list = []
        feature = self.data.columns[1:]
        for index, row in self.data.iterrows():
            row_df = pd.DataFrame(row).T
            mat = self.data_to_matrix(row_df)
            mat_list.append(mat)
        return mat_list, feature

    def cal_distance(self, mat_list, feature):
        manhattan_distance = lambda x, y: np.abs(x - y)
        # 得到第几条数据
        match_data = self.data[self.data['FLOOD_ID'] == self.id]
        assert not match_data.empty, "输入id查找到了空值"
        mat = self.data_to_matrix(match_data)
        _data = self.data[:]  # 使用切片操作重新拷贝一个对象，否则_data就是原对象的一个引用，对其修改会影响到原来的对象。
        distance_matrix = []
        for k in range(mat.shape[0]): # K表示特征的数量
            distance_list = []
            for j in range(len(mat_list)):
                d, cost_matrix, acc_cost_matrix, path = dtw(mat[k], mat_list[j][k], dist=manhattan_distance)
                distance_list.append(d)
            _data[feature[k]] = distance_list
        distance_matrix.append(_data)
        return distance_matrix

    def data_to_matrix(self, data):
        y = data.loc[data.index[0], 'RAINFALL_VALUE']
        y_size = len(y)
        feature = data.columns[1:]
        mat = np.zeros((len(feature), y_size))
        for j in range(len(feature)):
            x = data.loc[data.index[0], feature[j]]
            xlen = len(str(x).replace('[', '').replace(']', '').split(','))
            xlist = []
            if xlen == 1:
                xlist.append(x)
                row = np.pad(xlist, (y_size - 1, 0), 'constant', constant_values=(0, 0))
                mat[j, :] = row
            else:
                mat[j, :] = x
        return mat

    '''
            将上一步得到的dtw距离做归一化操作。
            distance_matrix: 上一步计算出来的的距离矩阵;[71x11] 包含ID
        '''

    def normalize_data(self, distance_matrix):
        i = distance_matrix[0]
        # 去除里面等于0的值进行归一化
        i = i[i.RAINFALL_VALUE >= 1e-6]
        # 记录ID
        ids = i.FLOOD_ID
        distance_std = i.apply(lambda x: (x - np.min(x)) / (np.max(x) - np.min(x)))
        distance_std['FLOOD_ID'] = ids
        return distance_std

    '''
            计算最终的的的的结果
            :param distance_std_list: 归一化后数值
            :param weights: 权重系统
            :return:
            '''
    def cal_final_value(self, distance_std_list):
        ids = np.array(distance_std_list['FLOOD_ID'])
        datas = distance_std_list[self.columns[1:]]
        datas = np.array(datas)
        weights = np.array(self.weights)
        res = np.dot(datas, weights)
        min_index = np.argsort(res)[:3]
        self.res_3_id = [ids[min_index[0]], ids[min_index[1]], ids[min_index[2]]]
        self.res_id = self.res_3_id[0]

    '''
        加权融合三条数据，作为预测结果。
        :return: 返回值为拟合的结果
    '''

    def merge(self):
        _data = self.data
        res_ids = self.res_3_id
        try:
            forecast1 = _data[_data['FLOOD_ID'] == res_ids[0]]['FLOW_VALUE'].values[0]
            forecast2 = _data[_data['FLOOD_ID'] == res_ids[1]]['FLOW_VALUE'].values[0]
            forecast3 = _data[_data['FLOOD_ID'] == res_ids[2]]['FLOW_VALUE'].values[0]
        except IndexError as e:
            logging.error(f"IndexError in merge: {e}")
            raise

        forecasts = [forecast1, forecast2, forecast3]
        lengths = [len(forecast1), len(forecast2), len(forecast3)]
        max_length = max(lengths)
        forecast = [None] * max_length
        for i in range(max_length):
            if i < lengths[0]:
                forecast[i] = forecasts[0][i] * 0.34 + forecasts[1][i] * 0.33 + forecasts[2][i] * 0.33
            elif i < lengths[1]:
                forecast[i] = forecasts[1][i] * 0.5 + forecasts[2][i] * 0.5
            else:
                forecast[i] = forecasts[2][i]
        return forecast

    def mdtw(self):
        mat, feature = self.get_mat_list()
        distance_matrix = self.cal_distance(mat, feature)
        distance_std = self.normalize_data(distance_matrix)
        self.cal_final_value(distance_std)
        merged_res = self.merge()
        assert self.res_id is not None, "匹配出错! res_id 为空"
        assert self.res_3_id is not None, "匹配出错! res_3_id 为空"
        result = {
            "matchId": self.id,
            "weights": self.weights,
            "sim3": self.res_3_id,
            "mergedRes": merged_res
        }

        sql1 = "insert into srv_match_res (results,match_time) values ('"+json.dumps(result, cls=NpEncoder)+"','"+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"');"
        db = DBUtils()
        db.exec(sql1)

        return json.dumps(result, cls=NpEncoder)
