用户模块（前端独立模块）

说明
- 本模块为“用户中心”功能的独立前端模块，包含：
  - `UserConsumptionQuery.vue`：用户个人消费明细查询（可按日期范围）
  - `UserRecentChanges.vue`：最近消费变化趋势（折线图 + 关键指标）
  - `UserModule.vue`：模块入口，包含选项卡

设计原则
- 不修改项目现有代码（路由/全局 API 文件均未更改）。
- 直接调用后端已实现的接口：
  - `/fastapi/consumption/query`（GET） - 查询个人消费明细和原始记录
  - `/fastapi/consumption/{studentId}/recent`（GET） - 近期消费变化与分析
- 使用 `localStorage.userInfo` 取得当前学号（`username` 字段）作为 `studentId`。

如何集成
1. 将此模块目录复制到项目（已在 `src/modules/user-module` 下）。
2. 在路由中添加一条（不由本模块自动添加，避免改动原代码）：

```js
// 在 src/router/index.js 的 routes 中新增
{
  path: '/user-module',
  name: 'UserModule',
  component: () => import('@/modules/user-module/UserModule.vue'),
  meta: { title: '用户中心' }
}
```

3. 在侧边栏或菜单中添加链接 `/user-module`。
4. 需要 ECharts：项目已有 `echarts`（如果没有，请安装：`npm i echarts`）。

注意
- 本模块直接使用 `axios` 请求 `/fastapi/...` 路径，前端已有代理会正确路由到 FastAPI 服务。
- 如果后端接口路径或返回字段改变，请在组件中相应调整解析逻辑。

如需，我可以帮你：
- 把路由自动注册（需要修改 `src/router/index.js`），
- 或把前端 API 文件 `src/api/user.js` 增加对应函数并在模块中使用（更一致）。
