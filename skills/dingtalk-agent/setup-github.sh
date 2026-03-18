#!/bin/bash

# DingTalk Agent GitHub Setup Script
# 这个脚本帮助你创建GitHub仓库并推送代码

echo "=== DingTalk Agent GitHub Setup ==="
echo ""

# 检查是否已安装Git
if ! command -v git &> /dev/null; then
    echo "错误: Git未安装，请先安装Git"
    exit 1
fi

# 检查是否已安装GitHub CLI
if command -v gh &> /dev/null; then
    echo "检测到GitHub CLI，正在创建仓库..."
    
    # 创建GitHub仓库
    gh repo create yunloli/dingtalk-agent --public --source=. --remote=origin --push
    
    echo ""
    echo "✅ GitHub仓库创建成功！"
    echo "仓库地址: https://github.com/yunloli/dingtalk-agent"
else
    echo "未检测到GitHub CLI，请手动创建仓库："
    echo ""
    echo "1. 访问 https://github.com/new"
    echo "2. 输入仓库名称: dingtalk-agent"
    echo "3. 选择公开仓库"
    echo "4. 创建仓库"
    echo ""
    echo "然后运行以下命令："
    echo "  git remote add origin https://github.com/yunloli/dingtalk-agent.git"
    echo "  git push -u origin master"
fi

echo ""
echo "=== 设置完成 ==="