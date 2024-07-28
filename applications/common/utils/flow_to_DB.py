import pandas as pd
from sqlalchemy import create_engine
import pymysql

# 读取 .xlsx 文件
file_path = 'D:\\postgraduate\\project\\MyPatternLibrary\\FloodFeature\\data\\屯溪数据\\1989\\流量数据\\屯溪.xls'    # 替换为你的文件路径
df = pd.read_excel(file_path)

# 假设文件的第一行为时间、流量
df.columns = ['time', 'flow']

# 转换时间格式
def convert_time_format(time_str):
    return pd.to_datetime(time_str, format='%Y%m%d%H')

df['time'] = df['time'].apply(convert_time_format)

# 添加 station_id 列并设置为 70111300
df['station_id'] = '70111300'

# 重命名列以匹配数据库字段名
df = df.rename(columns={'time': 'time', 'flow': 'flow_value'})

# 调整列的顺序
df = df[['station_id', 'time', 'flow_value']]

# 创建 MySQL 数据库连接
user = 'root'  # 替换为你的 MySQL 用户名
password = '111111'  # 替换为你的 MySQL 密码
host = 'localhost'  # 替换为你的 MySQL 主机地址
port = 3306  # 替换为你的 MySQL 端口号
database = 'flood'  # 替换为你的数据库名称

# 使用 sqlalchemy 创建数据库引擎
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

# 将数据写入 MySQL 数据库
table_name = 'flow_data'
df.to_sql(table_name, con=engine, if_exists='replace', index=False)

print(f"Data has been successfully written to the '{table_name}' table in the '{database}' database.")