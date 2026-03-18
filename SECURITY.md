# 安全说明

## 敏感文件

以下文件被 `.gitignore` 忽略，不会被提交到 Git 仓库：

1. **chat.log** - 运行日志，包含调试信息和 API 调用记录
2. **group_contexts.json** - 群组共享上下文，包含会话 ID
3. **sessions.json** - 用户模式开关状态
4. **dingtalk-agent.exe** - 编译后的可执行文件
5. **nul** - Windows 特殊文件

## 环境变量

敏感配置信息应通过环境变量设置：

- `OPENCODE_SERVER_PASSWORD` - OpenCode 服务器密码

## 注意事项

1. 不要将包含敏感信息的文件提交到 Git 仓库
2. 定期检查 `.gitignore` 配置是否正确
3. 如果意外提交了敏感文件，请立即从 Git 历史中删除
4. 考虑使用 Git Secrets 或类似工具防止敏感信息泄露

## 紧急处理

如果发现敏感信息泄露：

1. 立即轮换泄露的凭证
2. 从 Git 历史中删除敏感文件
3. 强制推送清理后的仓库
4. 通知相关团队成员