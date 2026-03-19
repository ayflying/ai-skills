# 数据库管理接口

## 1. 获取数据库列表
- **URL**: `/data?action=getData&table=databases`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |

## 2. 创建数据库
- **URL**: `/database?action=AddDatabase`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `name` | string | 数据库名 |
  | `db_user` | string | 数据库用户名 |
  | `password` | string | 密码 |
  | `address` | string | 访问地址 (通常 "127.0.0.1") |
  | `type` | string | 数据库类型 ("MySQL") |
  | `ps` | string | 备注 |

## 3. 删除数据库
- **URL**: `/database?action=DeleteDatabase`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int | 数据库 ID |
  | `name` | string | 数据库名 |

## 4. 修改数据库密码
- **URL**: `/database?action=ResDatabasePassword`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int | 数据库 ID |
  | `name` | string | 数据库名 |
  | `password` | string | 新密码 |

## 5. 获取数据库日志
- **URL**: `/database?action=GetDbErrorLog`
- **Method**: `POST`
