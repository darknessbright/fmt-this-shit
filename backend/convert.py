# backend/convert.py
"""Markdown 转 Word 转换核心模块"""
import os
import re
import subprocess
import uuid
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
import markdown as md_lib

# 常量配置
# 获取项目根目录（backend 的上级目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANDOC_PATH = os.path.join(PROJECT_ROOT, 'pandoc', 'pandoc.exe')
MMDC_PATH = os.path.join(PROJECT_ROOT, 'node_modules', '.bin', 'mmdc.cmd')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'backend', 'temp')

def ensure_temp_dir():
    """确保临时目录存在"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

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
                '-f', 'markdown+tex_math_dollars',  # 支持 \(...\) 和 \[...\] 格式
                '-t', 'docx',
                '--mathml',
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

    # 1. 提取并渲染 Mermaid 图表
    mermaid_images = render_mermaid_diagrams(markdown)

    # 2. 替换 Markdown 中的 mermaid 代码块为图片引用
    markdown_with_images = replace_mermaid_with_images(markdown, mermaid_images)

    # 3. 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    docx_filename = f'output_{timestamp}_{uuid.uuid4().hex[:8]}.docx'
    docx_path = os.path.join(TEMP_DIR, docx_filename)

    # 4. Pandoc 转换
    convert_with_pandoc(markdown_with_images, docx_path)

    # 5. python-docx 样式调整
    adjust_docx_styles(docx_path)

    # 6. 生成预览 HTML
    preview_html = generate_preview_html(markdown_with_images)

    return {
        'html': preview_html,
        'docx_url': f'/api/download/{docx_filename}',
        'pdf_url': None  # PDF 导出为可选功能
    }

def generate_preview_html(markdown):
    """
    生成预览 HTML

    Args:
        markdown: Markdown 内容

    Returns:
        str: HTML 内容
    """
    # 使用 python-markdown 生成 HTML
    html = md_lib.markdown(markdown, extensions=['extra', 'codehilite'])

    # 添加基础样式
    styled_html = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; padding: 20px;">
        {html}
        <style>
            h1, h2, h3, h4, h5, h6 {{ color: #333; margin-top: 20px; }}
            code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #666; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </div>
    """

    return styled_html
