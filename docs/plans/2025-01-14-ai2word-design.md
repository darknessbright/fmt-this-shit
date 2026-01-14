# AI2Word 设计文档

> 创建日期：2025-01-14
> 项目类型：个人使用 - AI/Markdown 转 Word 转换工具

## 项目概述

复刻 ai2word.online 的核心功能，构建一个精简实用的 AI 内容转 Word 工具。支持 LaTeX 数学公式、Mermaid 流程图、代码块、表格等转换，提供实时预览和 Word/PDF 导出功能。

**参考网站：**
- https://ai2word.online/
- https://www.yayacool.com/md2doc

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | Flask | Python Web 框架 |
| 核心转换 | Pandoc | Markdown/公式/表格转换 |
| 文档处理 | python-docx | Word 样式精细调整 |
| 图表渲染 | mermaid-cli | Mermaid 流程图转图片 |
| 前端编辑器 | CodeMirror | Markdown 输入编辑器 |
| 依赖管理 | venv + npm | Python 虚拟环境 + Node.js |

## 系统架构

### 项目结构

```
AI2Word/
├── .venv/              # Python 虚拟环境（独立运行环境）
├── pandoc/             # Pandoc 可执行文件（便携版）
├── mermaid-cli/        # mermaid-cli（npm 本地安装）
├── node_modules/       # Node.js 依赖
├── backend/            # Flask 后端
│   ├── app.py          # Flask 应用入口
│   ├── convert.py      # 转换逻辑
│   ├── temp/           # 临时文件存储
│   └── requirements.txt
├── frontend/           # 前端静态文件
│   ├── index.html      # 主页面
│   ├── css/
│   │   └── style.css   # 自定义样式
│   ├── js/
│   │   └── app.js      # 主应用逻辑
│   └── libs/           # 第三方库（本地化）
│       ├── codemirror/ # 代码编辑器
│       └── marked/     # Markdown 解析器（可选）
├── start.bat           # Windows 便捷启动脚本
├── requirements.txt    # Python 依赖
├── package.json        # Node.js 依赖
└── README.md           # 使用说明
```

### 数据流

```
用户输入 Markdown
       ↓
前端防抖（500ms）
       ↓
POST /api/convert
       ↓
后端处理：
  1. 提取 Mermaid 图表
  2. mermaid-cli 渲染为图片
  3. 替换 Markdown 中的图表为图片引用
  4. Pandoc 转换（公式、表格、代码块）
  5. python-docx 调整样式
       ↓
返回预览 HTML + 下载链接
       ↓
前端更新预览区
```

## 前端设计

### 界面布局

```
┌────────────────────────────────────────────┐
│  AI2Word              [导出 Word] [导出PDF] │
├──────────────────┬─────────────────────────┤
│                  │                         │
│  Markdown 输入    │    实时预览             │
│  (CodeMirror)     │    (Word 样式)         │
│                  │                         │
│                  │                         │
└──────────────────┴─────────────────────────┘
```

- **顶部栏**：左侧应用名称，右侧两个导出按钮
- **左侧 50%**：Markdown 输入编辑器，支持语法高亮、行号
- **右侧 50%**：实时预览区，显示转换后的 Word 效果
- **底部提示**："支持 Markdown、LaTeX 公式 ($E=mc^2$)、Mermaid 图表、代码块、表格转换"

### 实时预览机制

```javascript
// 防抖处理（500ms）
const debounceTimer = setTimeout(() => {
  fetch('/api/convert', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({markdown: editorContent})
  })
  .then(res => res.json())
  .then(data => {
    preview.innerHTML = data.html;
  });
}, 500);
```

### 前端依赖

**CodeMirror**
- 核心库：`lib/codemirror.js`
- Markdown 模式：`mode/markdown/markdown.js`
- 主题样式：`theme/default.css`

**Marked.js**（可选备用）
- 快速 Markdown 转 HTML 解析器

## 后端设计

### API 端点

#### 1. POST /api/convert
内容转换接口

**请求：**
```json
{
  "markdown": "# 标题\n\n内容..."
}
```

**响应：**
```json
{
  "html": "<div>预览HTML</div>",
  "docx_url": "/api/download/xxx.docx",
  "pdf_url": "/api/download/xxx.pdf"
}
```

#### 2. GET /api/download/<filename>
文件下载接口

**响应：** 文件流（application/octet-stream）

#### 3. GET /api/health
健康检查（可选）

### 转换流程

```python
def convert_markdown(markdown_content):
    # 1. 提取并渲染 Mermaid 图表
    mermaid_images = render_mermaid_diagrams(markdown_content)

    # 2. 替换 Markdown 中的 mermaid 代码块为图片引用
    markdown_with_images = replace_mermaid_with_images(markdown_content, mermaid_images)

    # 3. Pandoc 转换
    temp_md = write_temp_file(markdown_with_images)
    subprocess.run([
        'pandoc/pandoc.exe',
        temp_md,
        '-f', 'markdown',
        '-t', 'docx',
        '--mathml',
        '--extract-media=./temp',
        '-o', output_docx
    ])

    # 4. python-docx 样式调整
    adjust_docx_styles(output_docx)

    # 5. 生成 PDF（可选）
    generate_pdf(output_docx)

    return generate_preview_html(markdown_with_images)
```

### Mermaid 处理

```python
import re
import subprocess

def render_mermaid_diagrams(markdown):
    # 正则匹配 ```mermaid 代码块
    pattern = r'```mermaid\n(.*?)\n```'
    matches = re.findall(pattern, markdown, re.DOTALL)

    images = {}
    for i, mermaid_code in enumerate(matches):
        # 写入临时 .mmd 文件
        temp_mmd = f'temp/diagram_{i}.mmd'
        with open(temp_mmd, 'w') as f:
            f.write(mermaid_code)

        # 调用 mermaid-cli 渲染
        output_png = f'temp/diagram_{i}.png'
        subprocess.run([
            'node_modules/.bin/mmdc.cmd',
            '-i', temp_mmd,
            '-o', output_png
        ])

        images[mermaid_code] = output_png

    return images

def replace_mermaid_with_images(markdown, images):
    for code, img_path in images.items():
        markdown = markdown.replace(
            f'```mermaid\n{code}\n```',
            f'![mermaid]({img_path})'
        )
    return markdown
```

### 样式调整

```python
from docx import Document

def adjust_docx_styles(docx_path):
    doc = Document(docx_path)

    # 设置默认字体
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Microsoft YaHei'
    font.size = Pt(11)

    # 设置行间距
    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing = 1.5

    # 设置页边距
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)

    doc.save(docx_path)
```

## 启动脚本

### start.bat

```batch
@echo off
chcp 65001 >nul
echo ===================================
echo   AI2Word 启动中...
echo ===================================

REM 1. 检查 Python 虚拟环境
if not exist .venv (
    echo [1/5] 创建 Python 虚拟环境...
    python -m venv .venv
) else (
    echo [1/5] Python 虚拟环境已存在
)

REM 2. 激活虚拟环境并安装依赖
echo [2/5] 检查 Python 依赖...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt

REM 3. 检查 Pandoc
if not exist pandoc\pandoc.exe (
    echo [3/5] 警告: 未找到 pandoc.exe
    echo       请从 https://pandoc.org/installing.html 下载便携版
    echo       解压到 pandoc/ 目录
    pause
    exit
) else (
    echo [3/5] Pandoc 已就绪
)

REM 4. 检查 mermaid-cli
if not exist node_modules\.bin\mmdc.cmd (
    echo [4/5] 安装 mermaid-cli...
    npm install @mermaid-js/mermaid-cli
) else (
    echo [4/5] mermaid-cli 已就绪
)

REM 5. 启动 Flask 服务
echo [5/5] 启动 Flask 服务...
echo.
echo 服务地址: http://localhost:5678
echo 按 Ctrl+C 停止服务
echo.

start http://localhost:5678
.venv\Scripts\python backend/app.py

pause
```

## 依赖清单

### Python 依赖（requirements.txt）

```
Flask==3.0.0
python-docx==1.1.0
markdown==3.5.1
```

### Node.js 依赖（package.json）

```json
{
  "name": "ai2word",
  "version": "1.0.0",
  "dependencies": {
    "@mermaid-js/mermaid-cli": "^10.6.1"
  }
}
```

### 外部工具（需手动下载）

**Pandoc 便携版**
- 下载地址：https://pandoc.org/installing.html
- 解压到 `pandoc/` 目录
- 确保包含 `pandoc.exe`

## 配置说明

### Flask 配置

```python
# backend/app.py
from flask import Flask, send_file, request, jsonify
from convert import convert_markdown

app = Flask(__name__, static_folder='../frontend')

@app.route('/')
def index():
    return send_file('../frontend/index.html')

@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.json
    markdown = data.get('markdown', '')
    result = convert_markdown(markdown)
    return jsonify(result)

@app.route('/api/download/<filename>')
def download(filename):
    return send_file(f'temp/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5678, debug=True)
```

## 功能清单

### 支持的转换

- ✅ Markdown 基础语法（标题、列表、引用、粗体、斜体）
- ✅ LaTeX 数学公式（`$E=mc^2$`、`$$\int_0^1 x dx$$`）
- ✅ 表格（支持对齐、合并单元格）
- ✅ 代码块（语法高亮）
- ✅ Mermaid 流程图（渲染为图片）
- ✅ 图片插入

### 导出格式

- ✅ Word (.docx)
- ✅ PDF

### 不需要的功能

- ❌ 用户登录/注册
- ❌ 付费会员
- ❌ 用户反馈
- ❌ 微信群二维码
- ❌ 竞品对比
- ❌ 多种样式模板（使用统一默认样式）

## 实施计划

1. **环境搭建**
   - 创建项目结构
   - 配置虚拟环境
   - 下载 Pandoc 便携版

2. **后端开发**
   - Flask 基础框架
   - Pandoc 转换集成
   - Mermaid 渲染处理
   - python-docx 样式调整

3. **前端开发**
   - 页面布局
   - CodeMirror 集成
   - 实时预览功能
   - 导出按钮

4. **测试与优化**
   - 功能测试
   - 性能优化
   - 离线使用验证

## 注意事项

1. **端口冲突**：使用 5678 端口避免与常见服务冲突
2. **离线使用**：所有前端依赖本地化，无需 CDN
3. **临时文件清理**：定期清理 `backend/temp/` 目录下的过期文件
4. **跨平台**：目前优先支持 Windows（start.bat），后续可扩展 Linux/Mac
