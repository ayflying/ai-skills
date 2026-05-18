# gitea-weekly-report

生成一个或多个 Gitea 组织的周报：逐个抓取组织仓库，遍历仓库全部分支提交，按 commit SHA 去重，过滤技术噪音，并转换成用户能看懂的功能点。

## 安装

```bash
npx skills add ayflying/ai-skills --skill gitea-weekly-report
```

## 使用要点

- 支持多个组织名或组织 URL，例如 `esm`、`game_server`。
- 默认“上周”按自然周计算：上周一 `00:00:00` 到本周一 `00:00:00`。
- 仓库列表接口失败时，改用 `/repos/search` 并按 `owner.login == org` 过滤。
- 每个仓库必须先读取分支列表，再遍历所有分支 commits。
- 输出正式周报前会做提交数量校验和前 7 天 lookback 检查。

详细规则见 [SKILL.md](SKILL.md)。
