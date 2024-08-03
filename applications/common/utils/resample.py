import pandas as pd


def resample_time_series(data, index_column='time', sample_rate='h', fill_method='spline', order=3, start_time=None,
                         end_time=None):
    """
    对时间序列数据按指定的采样率进行重采样并填充。

    参数:
    - data: 带有日期时间列的pandas.DataFrame。
    - index_column: 日期时间列的名称。
    - sample_rate: 采样率（'h' 表示每小时）。
    - fill_method: 填充缺失数据的方法（'pad', 'bfill', 'interpolate', 'spline'）。
    - order: 样条插值的阶数（默认为3，即三次样条插值）。
    - start_time: 重采样的开始时间。
    - end_time: 重采样的结束时间。

    返回:
    - resampled_data: 重采样后的pandas.DataFrame。
    """
    # 确认日期时间列存在
    correct_index_column = next((col for col in data.columns if col.lower() == index_column.lower()), None)
    if correct_index_column is None:
        raise ValueError(f"指定的时间列 '{index_column}' 不存在于DataFrame中。请检查列名是否正确。")

    # 设置日期时间列为索引并转换格式
    data[correct_index_column] = pd.to_datetime(data[correct_index_column])
    data.set_index(correct_index_column, inplace=True)

    # 重采样并使用平均值进行聚合
    resampled_data = data.resample(sample_rate).mean()

    # 使用 ffill() 和 bfill() 替代已弃用的 fillna() 方法进行前向和后向填充
    resampled_data.ffill(inplace=True)  # 前向填充
    resampled_data.bfill(inplace=True)  # 后向填充

    # 应用指定的插值方法
    if fill_method == 'spline':
        resampled_data = resampled_data.interpolate(method='spline', order=order)
    elif fill_method in ['pad', 'bfill', 'interpolate']:
        resampled_data = resampled_data.interpolate(method=fill_method)
    else:
        raise ValueError("不支持的填充方法。请选择 'pad', 'bfill', 'interpolate', 或 'spline'。")

    # 根据提供的开始和结束时间进行重索引
    if start_time and end_time:
        full_index = pd.date_range(start=start_time, end=end_time, freq=sample_rate)
        resampled_data = resampled_data.reindex(full_index)
        resampled_data.ffill(inplace=True)
        resampled_data.bfill(inplace=True)

    # 重置索引并将时间列恢复为普通列
    resampled_data.reset_index(inplace=True)
    resampled_data.rename(columns={'index': index_column}, inplace=True)

    return resampled_data
