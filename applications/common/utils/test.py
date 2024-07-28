import pandas as pd
import datetime




csv_file_path = 'D:\postgraduate\project\PatternLibrary\data\\flow_data.csv'
data = pd.read_csv(csv_file_path, header=0, names=['Time', 'FlowValue'])
print("csv文件里的数据是")
print(data)
df = pd.DataFrame(data)
startId = '2021-12-20 16:00:00'
endId = '2021-12-21 10:00:00'
# 过滤出在开始时间和结束时间之间的数据
filtered_df = df[(df['Time'] >= startId) & (df['Time'] <= endId)]
# 显示结果
print("过滤后的数据")
print(filtered_df)

peaks = [5, 10]
slice_res = {}
duration = 5
# 确保时间列是 datetime 类型
data['Time'] = pd.to_datetime(data['Time'])
print("csv文件里的时间数据是")
print(data['Time'])

left_date = data.loc[0]['Time']
right_date = data.loc[data.shape[0] - 1]['Time']
for p in peaks:
    peak_time = data.loc[p]['Time']
    start_time = peak_time - datetime.timedelta(days=duration / 2)
    end_time = peak_time + datetime.timedelta(days=duration / 2)
    if start_time < left_date:  # 防止超出边界
        start_time = left_date
    if end_time > right_date:
        end_time = right_date
    slice_res[p] = {
        "start_date": start_time,
        "end_date": end_time,
        "peak_date": peak_time
    }
# print('划分结果：\n', slice_res)
print(slice_res)
# for res in slice_res:
#     print("峰值时间：{}".format(slice_res[res]['peak_date'])+'\t'+"开始时间：{}".format(slice_res[res]['start_date'])+'\t'+"结束时间：{}".format(slice_res[res]['end_date']))
