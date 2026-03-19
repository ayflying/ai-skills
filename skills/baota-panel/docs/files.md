# 文件与终端管理接口

## 1. 获取目录列表
- **URL**: `/files?action=GetDir`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `path` | string | 绝对路径 |

## 2. 创建目录
- **URL**: `/files?action=CreateDir`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `path` | string | 要创建的绝对路径 |

## 3. 写入文件
- **URL**: `/files?action=WriteFile`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `path` | string | 绝对文件路径 |
  | `data` | string | Base64 编码后的文件文本内容 |

## 4. 读取文件内容
- **URL**: `/files?action=GetFileBody`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `path` | string | 绝对路径 |

## 5. 执行 Shell 命令
在服务器上执行 bash 命令。

- **URL**: `/files?action=ExecShell`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `command` | string | 要执行的 shell 指令 |
