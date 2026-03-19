# 数据库管理接口

## 1. 获取数据库列表
- **URL**: `/data?action=getData&table=databases`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |
