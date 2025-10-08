# THU CS2 Web 对战平台 - 项目管理

## 1. 项目概述

本文件用于跟踪 THU CS2 Web 对战平台的开发进度，管理待办事项（TODO），并协调开发任务。所有内容基于 [PRD.md](./prd.md) 中定义的需求和里程碑。

## 2. 里程碑与进度

根据 PRD，项目分为四个核心里程碑（MVP）。

- **当前日期**: 2025-10-06

| 里程碑 | 状态 | 预计完成日期 | 负责人 |
| :--- | :--- | :--- | :--- |
| **M1: 基础功能 (1 周)** | ⏳ **进行中** | 2025-10-13 | @developer |
| **M2: 核心匹配流程 (2 周)** | 📋 **待开始** | 2025-10-27 | @developer |
| **M3: 游戏服务器集成 (2 周)** | 📋 **待开始** | 2025-11-10 | @developer |
| **M4: 数据与统计 (1 周)** | 📋 **待开始** | 2025-11-17 | @developer |

---

## 3. 待办事项 (TODO List)

### M1: 基础功能 (预计完成: 2025-10-13)

-   [x] **产品需求文档 (PRD)** - `docs/prd.md`
-   [x] **数据库模型设计**
    -   [x] `User` 模型 (`backend/models/user.py`) - `elo` 字段已添加。
    -   [x] `Match` 模型 (`backend/models/match.py`) - 核心模型已创建。
    -   [x] `Session` 模型 (`backend/models/session.py`) - 用于缓存
    -   [ ] 数据库初始化脚本 (`backend/models/database.py`)
-   [x] **用户认证 (Auth)**
    -   [x] Steam OpenID 登录后端逻辑 (`backend/routers/auth.py`) - 登录及回调逻辑已实现。
    -   [x] 登录回调处理
    -   [ ] 前端登录页面 (`src/components/LoginPage.vue`)
    -   [ ] 用户状态管理 (Pinia/Vuex) (`src/stores/auth.js`)
-   [x] **管理员后台**
    -   [x] 用户审核接口 (`backend/routers/admin.py`)
    -   [ ] 基础的前端审核页面 (`src/components/AdminPanel.vue`)

### M2: 核心匹配流程 (预计完成: 2025-10-27)

-   [ ] **匹配后端逻辑**
    -   [ ] 加入/离开匹配队列接口 (`backend/routers/matching.py`)
    -   [ ] 使用 Redis 实现匹配队列
    -   [ ] 匹配算法实现（寻找10人）
-   [ ] **游戏房间创建**
    -   [ ] 队长选举与选人逻辑 (`backend/routers/game.py`)
    -   [ ] 地图 Veto 逻辑 (2-3-1 Ban)
    -   [ ] 选边逻辑
-   [ ] **前端匹配与房间界面**
    -   [ ] 匹配按钮与状态显示 (`src/components/MatchingSystem.vue`)
    -   [ ] 比赛确认模态框 (`src/components/MatchConfirmModal.vue`)
    -   [ ] 选人/Veto 界面 (`src/views/GameRoom.vue`)
    -   [ ] WebSocket 集成，用于实时状态更新 (`src/api/client.js`)

### M3: 游戏服务器集成 (预计完成: 2025-11-10)

-   [ ] **后端服务器通信**
    -   [ ] 与预设游戏服务器的通信逻辑 (`backend/game/start_server.py`)
    -   [ ] 发送比赛配置至 Matchzy 插件
    -   [ ] 获取服务器连接信息并返回给前端
-   [ ] **Matchzy 回调处理**
    -   [ ] 实现回调接口 (`backend/routers/events_callback.py`)
    -   [ ] 解析 `final_result` 等关键事件
    -   [ ] 将原始比赛数据存入 `matchzy_stats_*` 表
-   [ ] **前端游戏界面**
    -   [ ] 显示服务器连接信息 (`src/views/GameRoom.vue`)
    -   [ ] 比赛状态实时更新（如 `live`, `finished`）

### M4: 数据与统计 (预计完成: 2025-11-17)

-   [ ] **赛后处理**
    -   [ ] Elo 积分计算逻辑 (`backend/utils/tasks.py`)
    -   [ ] 异步任务更新用户 Elo
-   [ ] **数据统计 API**
    -   [ ] 个人生涯统计接口 (`backend/routers/matchzy.py`)
    -   [ ] 排行榜接口
    -   [ ] 个人比赛历史接口
-   [ ] **前端数据展示**
    -   [ ] 个人资料页 (`src/components/ProfilePage.vue`)
    -   [ ] 排行榜页面
    -   [ ] 比赛详情页

---

## 4. 风险与备注

- **开发重点**: 严格遵循 MVP 范围，优先保证核心流程（匹配 -> 进服 -> 结算）的通畅。
- **外部依赖**: Matchzy 插件的稳定性和回调机制是关键，需要充分测试。
- **前端状态管理**: 比赛流程中状态复杂（`picking`, `veto`, `live`），需精心设计 Pinia/Vuex 的 store 结构。
