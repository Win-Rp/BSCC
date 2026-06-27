# BSCC 标书查重系统 (Bid Document Check Center)

智能标书对比工具，通过 AI 算法识别标书间的相似度、改写痕迹及语义关联，帮助用户快速排查围标风险。

## 🚀 项目结构

- **[frontend/](file:///d:/Rp/Dev/AICode/BSCC/frontend)**: 基于 Vue 3 + Element Plus + ECharts 构建的现代化前端界面。
- **[backend/](file:///d:/Rp/Dev/AICode/BSCC/backend)**: 基于 FastAPI + SQLite 构建的高性能后端 API。
- **[docs/](file:///d:/Rp/Dev/AICode/BSCC/docs)**: 包含 API 设计、数据库模型及用户流程等项目文档。

## 🛠️ 快速启动

### 后端启动 (Python 3.9+)

1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动服务：
   ```bash
   python -m app.main
   ```
   *服务将运行在: `http://127.0.0.1:8000`*

### 前端启动 (Node.js 18+)

1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   *界面访问地址: `http://127.0.0.1:5173`*

## ✨ 核心功能

- **步骤导航系统**: 顶部的时间线导航实时展示任务进度。
- **多维度查重**: 支持完全匹配、改写识别、语义相似度分析及元数据比对。
- **可视化大盘**: 通过 ECharts 环形图和横向柱状图展示关键字命中率和相似度排行，直观识别高风险标书。
- **原文比对**: 支持 DOCX 和 PDF 的左右分屏高亮比对，侧边抽屉快速定位重复片段。
- **任务找回机制**: 通过任务 ID，用户可以在 7 天内随时找回并查看历史查重结果。
- **后台管理系统**: 独立的 `/admin` 工作台，支持订单管理、任务重试、数据清理、以及系统级配置（查重阈值、保留期限、首页动态标签等）的热更新。
- **支付解锁**: 集成支付模拟流程，解锁详细比对报告。

## 📚 开发者文档

- [API 规范](file:///d:/Rp/Dev/AICode/BSCC/docs/api-spec.md)
- [需求文档](file:///d:/Rp/Dev/AICode/BSCC/docs/requirements.md)
- [用户流程](file:///d:/Rp/Dev/AICode/BSCC/docs/user-flows.md)
