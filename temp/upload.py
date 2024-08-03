import pandas as pd
from sqlalchemy import create_engine

# 数据库配置
user = 'root'
password = '111111'  # 确保密码用字符串格式
host = 'localhost'
port = 3306
database = 'flood_analysis'

# 创建数据库连接引擎
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}')

# 指定的Excel文件路径
file_path = r'D:/postgraduate/知识引擎/SourceData/息县数据/xixian.xlsx'

# 读取Excel文件的实测数据_2020工作表
df_2020 = pd.read_excel(file_path, sheet_name='实测数据_2020', usecols=['时间', '息县区间面雨量'])

# 时间格式转换并重命名列以匹配数据库中的列名
df_2020['时间'] = pd.to_datetime(df_2020['时间']).dt.strftime('%Y-%m-%d %H:%M:%S')
df_2020.rename(columns={'时间': 'time', '息县区间面雨量': 'rain_value'}, inplace=True)
df_2020['station_id'] = 50100500  # 假设50100500是息县实测流量对应的站点ID
df_2020 = df_2020[['station_id', 'time', 'rain_value']]

# 导入2020年数据到数据库的flow_data表
df_2020.to_sql('rain_data', con=engine, if_exists='append', index=False)

# 读取Excel文件的实测数据_2021工作表
df_2021 = pd.read_excel(file_path, sheet_name='实测数据_2021', usecols=['时间', '息县区间面雨量'])

# 时间格式转换并重命名列以匹配数据库中的列名
df_2021['时间'] = pd.to_datetime(df_2021['时间']).dt.strftime('%Y-%m-%d %H:%M:%S')
df_2021.rename(columns={'时间': 'time', '息县区间面雨量': 'rain_value'}, inplace=True)
df_2021['station_id'] = 50100500  # 假设50100500是息县实测流量对应的站点ID
df_2021 = df_2021[['station_id', 'time', 'rain_value']]

# 导入2021年数据到数据库的flow_data表
df_2021.to_sql('rain_data', con=engine, if_exists='append', index=False)

print("数据导入完成")
