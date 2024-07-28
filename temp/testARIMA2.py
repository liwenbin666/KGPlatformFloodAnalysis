import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

from statsmodels.tsa.stattools import adfuller

# 生成模拟数据，以小时为间隔
np.random.seed(0)
dates = pd.date_range(start='2022-01-01', end='2022-01-31', freq='H')
n = len(dates)
flow = np.random.normal(loc=100, scale=50, size=n).cumsum()  # 修改流量的标准差以增加波动性
rainfall = np.random.normal(loc=50, scale=20, size=n).cumsum()  # 修改雨量的标准差以增加波动性

data = pd.DataFrame({'timestamp': dates, 'flow': flow, 'rainfall': rainfall})
data.set_index('timestamp', inplace=True)

# 明确设置频率
data.index.freq = 'H'

# 检查数据的前几行
print(data.head())

# 检查缺失值
print(data.isnull().sum())

# 差分处理使流量数据平稳
flow_diff = data['flow'].diff().dropna()

# 检查流量数据的平稳性
result = adfuller(flow_diff)
print('ADF Statistic for flow: %f' % result[0])
print('p-value for flow: %f' % result[1])

# 差分处理使雨量数据平稳
rain_diff = data['rainfall'].diff().dropna()

# 检查雨量数据的平稳性
result = adfuller(rain_diff)
print('ADF Statistic for rainfall: %f' % result[0])
print('p-value for rainfall: %f' % result[1])

# 拟合ARIMAX模型，将雨量数据作为外生变量
model = ARIMA(data['flow'], exog=data['rainfall'], order=(5, 1, 0))
model_fit = model.fit()

# 残差分析
residuals = model_fit.resid
plt.figure()
plt.plot(residuals)
plt.title('Residuals from ARIMAX Model')
plt.show()

# 检测异常
threshold = 2 * residuals.std()  # 设置一个阈值
anomalies = residuals[np.abs(residuals) > threshold]

# 显示异常
print(anomalies)

# 检测洪水事件的开始和结束时间
floods = []
for anomaly in anomalies.index:
    start = anomaly
    end = anomaly
    # 向前找开始时间
    while start > data.index[0] and data.loc[start, 'flow'] > data['flow'].mean():
        start -= pd.Timedelta(hours=1)
    start += pd.Timedelta(hours=1)

    # 向后找结束时间
    while end < data.index[-1] and data.loc[end, 'flow'] > data['flow'].mean():
        end += pd.Timedelta(hours=1)
    end -= pd.Timedelta(hours=1)

    floods.append((start, end))

# 去重并显示洪水事件
floods = list(set(floods))
print("Flood events (start, end):")
for flood in floods:
    print(flood)

# 可视化异常和洪水事件
plt.figure()
plt.plot(data['flow'], label='Flow')
plt.scatter(anomalies.index, data.loc[anomalies.index, 'flow'], color='red', label='Anomalies')
for start, end in floods:
    plt.axvspan(start, end, color='yellow', alpha=0.3)
plt.legend()
plt.title('Anomalies and Flood Events in Flow Time Series with Rainfall as Exogenous Variable')
plt.show()
