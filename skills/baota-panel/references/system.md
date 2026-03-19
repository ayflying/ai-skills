# 系统状态接口

## 1. 获取系统状态汇总
- **URL**: `/system?action=GetSystemTotal`
- **Method**: `POST`
- **说明**: 获取 CPU、内存、网络等系统状态信息
- **响应示例**:
  ```json
  {
    "status": true,
    "data": {
      "cpu": {"used": 15.6, "info": "Intel Xeon"},
      "mem": {"used": 2048, "total": 8192, "percent": 25},
      "disk": {"used": 50, "total": 500, "percent": 10},
      "load": [0.15, 0.10, 0.05]
    }
  }
  ```

## 2. 获取磁盘信息
- **URL**: `/system?action=GetDiskInfo`
- **Method**: `POST`
- **说明**: 获取各分区磁盘使用情况

## 3. 获取网络状态
- **URL**: `/system?action=GetNetWork`
- **Method**: `POST`
- **说明**: 获取网络接口状态和流量统计

## 4. 获取任务数量
- **URL**: `/ajax?action=GetTaskCount`
- **Method**: `POST`
- **说明**: 获取当前队列中的任务数量

## 5. 更新面板
- **URL**: `/ajax?action=UpdatePanel`
- **Method**: `POST`
- **说明**: 检查并更新面板到最新版本

## 6. 获取面板日志
- **URL**: `/data?action=getData&table=logs`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |
