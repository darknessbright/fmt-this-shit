# backend/convert.py
"""Markdown 转 Word 转换核心模块"""
import os
import sys
import re
import subprocess
import uuid
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches

# 常量配置
# 获取项目根目录（支持开发和打包环境）
if getattr(sys, 'frozen', False):
    # 打包后的 exe 环境：使用 exe 所在目录
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    # 开发环境：使用 __file__ 的上级目录
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 动态检测 Pandoc 路径
PANDOC_PATH = os.path.join(PROJECT_ROOT, 'pandoc', 'pandoc.exe')
if not os.path.exists(PANDOC_PATH):
    raise FileNotFoundError(
        f"Pandoc 可执行文件不存在: {PANDOC_PATH}\n"
        f"请确保便携包完整，或从 https://pandoc.org/installing.html 下载"
    )

# 动态检测 mermaid-cli 路径
MMDC_PATH = os.path.join(PROJECT_ROOT, 'node_modules', '.bin', 'mmdc.cmd')
if not os.path.exists(MMDC_PATH):
    raise FileNotFoundError(
        f"mermaid-cli 不存在: {MMDC_PATH}\n"
        f"请运行: npm install @mermaid-js/mermaid-cli"
    )

TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')

def ensure_temp_dir():
    """确保临时目录存在"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def preprocess_latex(markdown):
    """
    预处理：保护已有 LaTeX 公式，避免被后续处理破坏

    只保护 AI 输出中已有的 LaTeX 格式，不添加任何新格式。

    Args:
        markdown: 原始 Markdown 内容

    Returns:
        str: 预处理后的 Markdown
    """
    # 标准化换行符为 \n（处理 Windows \r\n）
    markdown = markdown.replace('\r\n', '\n').replace('\r', '\n')

    # 保护已有 LaTeX 公式，避免被后续处理破坏
    # 使用占位符暂时替换，处理完后再恢复
    latex_blocks = []
    def save_latex_block(match):
        latex_blocks.append(match.group(0))
        return f"LATEXBLOCKPLACEHOLDERXYZ{len(latex_blocks)-1}PLACEHOLDERXYZ"

    # 保护 \[ ... \] (display math) - 跨行匹配
    display_open = re.escape(r'\[')
    display_close = re.escape(r'\]')
    display_pattern = display_open + r'.*?' + display_close
    markdown = re.sub(display_pattern, save_latex_block, markdown, flags=re.DOTALL)

    # 保护 \( ... \) (inline math)
    inline_open = re.escape(r'\(')
    inline_close = re.escape(r'\)')
    inline_pattern = inline_open + r'.*?' + inline_close
    markdown = re.sub(inline_pattern, save_latex_block, markdown)

    # 保护 $ ... $ 和 $$ ... $$ 格式
    markdown = re.sub(r'\$[^$\n]+?\$', save_latex_block, markdown)
    markdown = re.sub(r'\$\$[^$]+?\$\$', save_latex_block, markdown, flags=re.DOTALL)

    return markdown, latex_blocks

def render_mermaid_diagrams(markdown):
    """
    渲染 Mermaid 流程图为图片

    Args:
        markdown: Markdown 内容

    Returns:
        dict: {mermaid_code: image_path} 映射
    """
    # 正则匹配 ```mermaid 代码块
    pattern = r'```mermaid\n(.*?)\n```'
    matches = re.findall(pattern, markdown, re.DOTALL)

    images = {}
    ensure_temp_dir()

    for i, mermaid_code in enumerate(matches):
        # 写入临时 .mmd 文件
        temp_mmd = os.path.join(TEMP_DIR, f'diagram_{i}_{uuid.uuid4().hex[:8]}.mmd')
        with open(temp_mmd, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)

        # 调用 mermaid-cli 渲染
        output_png = os.path.join(TEMP_DIR, f'diagram_{i}_{uuid.uuid4().hex[:8]}.png')

        try:
            subprocess.run(
                [MMDC_PATH, '-i', temp_mmd, '-o', output_png],
                check=True,
                capture_output=True,
                text=True,
                shell=True
            )
            images[mermaid_code] = output_png
        except subprocess.CalledProcessError as e:
            print(f"Mermaid 渲染失败: {e.stderr}")
            # 即使失败也添加占位符
            images[mermaid_code] = None

    return images

def replace_mermaid_with_images(markdown, images):
    """
    替换 Markdown 中的 mermaid 代码块为图片引用

    Args:
        markdown: 原始 Markdown 内容
        images: {mermaid_code: image_path} 映射

    Returns:
        str: 替换后的 Markdown
    """
    for code, img_path in images.items():
        if img_path:
            # 使用相对路径引用图片
            relative_path = os.path.basename(img_path)
            markdown = markdown.replace(
                f'```mermaid\n{code}\n```',
                f'![mermaid diagram](temp/{relative_path})\n'
            )
        else:
            # 渲染失败时保留原始代码
            markdown = markdown.replace(
                f'```mermaid\n{code}\n```',
                f'> ⚠️ Mermaid 图表渲染失败\n```\n{code}\n```\n'
            )
    return markdown

def convert_with_pandoc(markdown, output_path):
    """
    使用 Pandoc 将 Markdown 转换为 DOCX

    Args:
        markdown: Markdown 内容
        output_path: 输出 DOCX 文件路径
    """
    # 写入临时 Markdown 文件
    temp_md = os.path.join(TEMP_DIR, f'temp_{uuid.uuid4().hex[:8]}.md')
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(markdown)

    try:
        subprocess.run(
            [
                PANDOC_PATH,
                temp_md,
                '-f', 'markdown+tex_math_dollars+tex_math_single_backslash',  # 支持 \(...\) 和 \[...\] 格式
                '-t', 'docx',
                '-o', output_path
            ],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Pandoc 转换失败: {e.stderr}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_md):
            os.remove(temp_md)

def adjust_docx_styles(docx_path):
    """
    调整 Word 文档样式

    Args:
        docx_path: DOCX 文件路径
    """
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

def convert_markdown(markdown):
    """
    主转换函数：将 Markdown 转换为 Word 文档并生成预览

    Args:
        markdown: Markdown 内容

    Returns:
        dict: {
            'html': 预览 HTML,
            'docx_url': DOCX 下载链接,
            'pdf_url': PDF 下载链接（可选）
        }
    """
    ensure_temp_dir()

    # 1. 预处理：保护已有 LaTeX 公式
    markdown, latex_blocks = preprocess_latex(markdown)

    # 2. 提取并渲染 Mermaid 图表
    mermaid_images = render_mermaid_diagrams(markdown)

    # 3. 替换 Markdown 中的 mermaid 代码块为图片引用
    markdown_with_images = replace_mermaid_with_images(markdown, mermaid_images)

    # 4. 为Pandoc恢复LaTeX公式（用于Pandoc转换）
    # Pandoc需要 \(...\) 和 \[...\] 格式
    markdown_for_pandoc = markdown_with_images
    for i, block in enumerate(latex_blocks):
        markdown_for_pandoc = markdown_for_pandoc.replace(f"LATEXBLOCKPLACEHOLDERXYZ{i}PLACEHOLDERXYZ", block)

    # 注意：markdown_with_images 仍然包含占位符，用于HTML生成

    # 5. 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    docx_filename = f'output_{timestamp}_{uuid.uuid4().hex[:8]}.docx'
    docx_path = os.path.join(TEMP_DIR, docx_filename)

    # 6. Pandoc 转换（使用恢复LaTeX的版本）
    convert_with_pandoc(markdown_for_pandoc, docx_path)

    # 7. python-docx 样式调整
    adjust_docx_styles(docx_path)

    # 8. 生成预览 HTML（使用包含占位符的版本）
    preview_html = generate_preview_html(markdown_with_images, latex_blocks)

    return {
        'html': preview_html,
        'docx_url': f'/api/download/{docx_filename}',
        'pdf_url': None  # PDF 导出为可选功能
    }

def generate_preview_html(markdown, latex_blocks):
    """
    生成预览 HTML（保留 LaTeX 公式供 MathJax 渲染）

    Args:
        markdown: Markdown 内容
        latex_blocks: LaTeX 公式块列表

    Returns:
        str: HTML 内容
    """
    # 使用简单处理，避免 markdown 库破坏 LaTeX 公式
    html = simple_markdown_to_html(markdown)

    # 恢复 LaTeX 公式占位符（在 markdown 转换之后）
    for i, block in enumerate(latex_blocks):
        html = html.replace(f"LATEXBLOCKPLACEHOLDERXYZ{i}PLACEHOLDERXYZ", block)

    # 添加基础样式
    styled_html = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; padding: 20px;">
        {html}
        <style>
            h1, h2, h3, h4, h5, h6 {{ color: #333; margin-top: 20px; margin-bottom: 10px; }}
            code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Consolas', monospace; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #666; margin: 10px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            img {{ max-width: 100%; height: auto; }}
            p {{ margin: 8px 0; }}
        </style>
    </div>
    """

    return styled_html

def simple_markdown_to_html(markdown):
    """
    简单的 Markdown 转 HTML

    Args:
        markdown: Markdown 内容

    Returns:
        str: HTML 内容
    """
    lines = markdown.split('\n')
    html_lines = []
    in_code_block = False
    code_lines = []
    in_display_math = False
    in_table = False
    table_rows = []

    for line in lines:
        # 检测 display math 开始
        if line.strip() == r'\[':
            # 开始收集 display math（多行）
            in_display_math = True
            math_lines = []
            continue

        # 检测 display math 结束
        if line.strip() == r'\]':
            # 结束 display math，输出为一个块
            in_display_math = False
            math_content = r'\[' + '\n'.join(math_lines) + r'\]'
            html_lines.append(f'<p>{math_content}</p>')
            math_lines = []
            continue

        # 如果在 display math 中，收集行
        if in_display_math:
            math_lines.append(line)
            continue

        # 处理代码块
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                code_html = '<pre><code>' + '\n'.join(code_lines) + '</code></pre>'
                html_lines.append(code_html)
                in_code_block = False
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # 处理标题
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if 1 <= level <= 6:
                text = line.lstrip('#').strip()
                html_lines.append(f'<h{level}>{text}</h{level}>')
                continue

        # 处理表格（简化处理：检测连续的表格行）
        if '|' in line and line.strip():
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(line)
            continue
        elif in_table:
            # 表格结束（没有 | 了）
            if '|' not in line:
                html_lines.append(render_table(table_rows))
                in_table = False
                table_rows = []
            # 继续处理当前行

        # 处理粗体和斜体
        # 如果行中包含LaTeX占位符，跳过斜体处理（避免破坏数学符号中的下划线）
        has_latex_placeholder = 'LATEXBLOCKPLACEHOLDERXYZ' in line
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        if not has_latex_placeholder:
            line = re.sub(r'_(.+?)_', r'<em>\1</em>', line)

        # 处理行内代码
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        # 处理空行
        if not line.strip():
            html_lines.append('<br>')
        else:
            html_lines.append(f'<p>{line}</p>')

    return '\n'.join(html_lines)

def render_table(rows):
    """渲染表格行为 HTML"""
    if not rows:
        return ''

    html = ['<table>']
    for i, row in enumerate(rows):
        cells = [cell.strip() for cell in row.split('|') if cell.strip()]
        if not cells:
            continue
        if i == 0 or all(re.match(r'^\s*[-:]+\s*$', cell) for cell in cells):
            # 跳过分隔行
            continue
        tag = 'th' if i == 0 else 'td'
        html.append('<tr>')
        for cell in cells:
            html.append(f'<{tag}>{cell}</{tag}>')
        html.append('</tr>')
    html.append('</table>')
    return '\n'.join(html)
