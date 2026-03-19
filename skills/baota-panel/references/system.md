# 系统管理接口

## 1. 获取系统概览信息
获取服务器资源使用情况（CPU、内存、负载、磁盘等）。

- **URL**: `/system?action=GetSystemTotal`
- **Method**: `POST`
- **参数**: 无 (仅公共参数)
- **返回**: 包含资源状态的详细 JSON。

## 2. 获取插件/软件列表
列出宝塔面板安装的所有软件及其状态。

- **URL**: `/plugin?action=get_soft_list`
- **Method**: `POST`
- **参数**: 无 (仅公共参数)
- **返回**: 软件列表 JSON。

## 3. 安装软件
- **URL**: `/plugin?action=install_plugin`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `s_name` | string | 软件名称 |
  | `version` | string | 软件版本 |

## 4. 卸载软件
- **URL**: `/plugin?action=un_install_plugin`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `s_name` | string | 软件名称 |
  | `version` | string | 软件版本 |

## 5. 更新软件
- **URL**: `/plugin?action=update_plugin`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `s_name` | string | 软件名称 |
  | `version` | string | 软件版本 |
