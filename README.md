# AI2Word

AI/Markdown 转 Word 转换工具

## 快速开始

双击 `start.bat` 启动应用

## 手动安装

1. 创建虚拟环境: `python -m venv .venv`
2. 安装 Python 依赖: `.venv\Scripts\pip install -r requirements.txt`
3. 下载 Pandoc: 从 https://pandoc.org/installing.html 下载便携版，解压到 `pandoc/` 目录
4. 安装 mermaid-cli: `npm install`
5. 启动服务: `.venv\Scripts\python backend/app.py`
6. 访问: http://localhost:5678

## 功能

- Markdown 转 Word/PDF
- LaTeX 数学公式支持
- Mermaid 流程图支持
- 实时预览
