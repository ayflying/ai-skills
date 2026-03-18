# GitHub 仓库设置指南

由于没有检测到 GitHub CLI，你需要手动创建 GitHub 仓库。

## 步骤

### 1. 创建 GitHub 仓库

1. 访问 [GitHub 新建仓库页面](https://github.com/new)
2. 输入仓库名称：`dingtalk-agent`
3. 描述：`钉钉机器人集成 OpenCode AI 技能`
4. 选择 **公开仓库** (Public)
5. 勾选 "Add a README file"（可选，我们已经有了）
6. 点击 "Create repository"

### 2. 推送代码到 GitHub

打开终端（命令行），执行以下命令：

```bash
# 进入项目目录
cd "D:\git\yunloli\game2\.agents\skills\dingtalk-agent"

# 添加远程仓库（将 your-username 替换为你的 GitHub 用户名）
git remote add origin https://github.com/your-username/dingtalk-agent.git

# 推送代码
git push -u origin master
```

### 3. 验证推送

访问 `https://github.com/your-username/dingtalk-agent` 查看你的仓库。

## 如果已经存在远程仓库

如果你已经创建了远程仓库，可以直接推送：

```bash
cd "D:\git\yunloli\game2\.agents\skills\dingtalk-agent"
git push -u origin master
```

## 常见问题

### Q: 提示 "remote origin already exists"
A: 运行以下命令移除旧的远程仓库：
```bash
git remote remove origin
git remote add origin https://github.com/your-username/dingtalk-agent.git
```

### Q: 推送时提示认证失败
A: 你需要配置 GitHub 认证：
1. 使用 Personal Access Token (PAT)
2. 或者使用 GitHub CLI 登录：`gh auth login`

### Q: 如何更新远程仓库地址
A: 运行以下命令：
```bash
git remote set-url origin https://github.com/your-username/dingtalk-agent.git
```

## 后续步骤

1. 在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加必要的秘密
2. 设置分支保护规则（可选）
3. 创建 Issue 模板和 Pull Request 模板（可选）