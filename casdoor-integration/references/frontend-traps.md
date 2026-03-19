# 前端构建陷阱：环境变量与静态编译

## 问题描述
配置了 `SOCIAL_AUTH_PROVIDERS=casdoor` 后，在开发模式 (`dev`) 下能看到登录按钮，但在 Docker 生产环境下，登录按钮却离奇消失。

## 根本原因
1. **静态编译固化**: Next.js、Vite 等框架在构建镜像（`npm run build`）时会进行静态页面优化。
2. **环境变量缺失**: 如果构建期（`docker build`）没有传入环境变量，前端代码逻辑 `providers.filter(p => env.PROVIDERS.includes(p.id))` 会被编译为“空数组”。
3. **运行时不更新**: 即使你在 `docker run` 时传入了变量，由于 HTML/JS 已经是静态编译好的，按钮依然不会显示。

## 解决方案
1. **构建期注入 (Build Args)**:
   - 在 `Dockerfile` 中定义 `ARG SOCIAL_AUTH_PROVIDERS`。
   - 在 `docker build` 命令中使用 `--build-arg SOCIAL_AUTH_PROVIDERS=casdoor`。
2. **代码健壮性**:
   - 如果后端环境变量（如 `BACKEND_CASDOOR_CLIENT_ID`）存在，前端应尝试自动显示按钮，而不是仅依赖单一的数组过滤器。
3. **强制检查**:
   - 在构建日志中检查 `NEXT_PUBLIC_...` 变量是否已正确写入 `.env` 或被 Webpack 注入。
