import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline


def resample_data(df, freq='H', method='cubic'):
    """
    重新采样时间序列数据并应用插值。
    参数：
    - df: DataFrame, 包含时间戳索引和至少一列数据。
    - freq: 字符串, 输出数据的频率（例如 'H' 表示每小时）。
    - method: 字符串, 指定插值方法（支持 'linear'、'cubic' 等）。
    返回：
    - DataFrame, 包含重新采样和插值后的数据。
    """
    # 确保时间戳是索引
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Index must be a DatetimeIndex.")

    # 创建新的时间索引
    time_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)

    # 根据选择的插值方法应用插值
    if method == 'cubic':
        # 三次样条插值
        interpolated_data = {}
        for column in df.columns:
            cs = CubicSpline(df.index.astype(np.int64), df[column])
            interpolated_data[column] = cs(time_index.astype(np.int64))
        df_interpolated = pd.DataFrame(interpolated_data, index=time_index)
    elif method == 'linear':
        # 线性插值
        df_interpolated = df.reindex(time_index.union(df.index)).interpolate(method='time').loc[time_index]
    else:
        raise ValueError("Unsupported interpolation method. Use 'linear' or 'cubic'.")

    return df_interpolated
