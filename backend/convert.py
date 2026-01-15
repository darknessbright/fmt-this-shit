# backend/convert.py
"""Markdown 转 Word 转换核心模块"""
import os
import re
import subprocess
import uuid
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches

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

def preprocess_latex(markdown):
    """
    智能预处理：自动识别并包裹数学符号

    检测以下模式并包裹为 \( ... \)：
    - 希腊字母：α, β, γ, θ, λ, μ, σ, ω, Δ, Σ, Π, Ω 等
    - 数学函数带下标/上标：s_i, x^2, k_{i+1} 等
    - 数学花体字母：\mathcal{W}, \mathcal{D} 等（但已包裹的跳过）
    - 数学符号：\dots, \ldots, \in, \leq, \geq, \neq, \approx 等
    - 已有 \( ... \) 或 \[ ... \] 包裹的跳过

    Args:
        markdown: 原始 Markdown 内容

    Returns:
        str: 预处理后的 Markdown
    """
    # 首先保护已有的 LaTeX 公式，避免重复处理
    # 使用更独特的占位符，避免被后续正则匹配
    latex_blocks = []
    def save_latex_block(match):
        latex_blocks.append(match.group(0))
        return f"LATEXBLOCKPLACEHOLDERXYZ{len(latex_blocks)-1}PLACEHOLDERXYZ"

    # 保护 \[ ... \] (display math)
    markdown = re.sub(r'\\\[.*?\\\]', save_latex_block, markdown, flags=re.DOTALL)

    # 保护 \( ... \) (inline math)
    markdown = re.sub(r'\\\(.*?\\\)', save_latex_block, markdown, flags=re.DOTALL)

    # 保护 $ ... $ (alternative inline math)
    markdown = re.sub(r'\$[^$\n]+?\$', save_latex_block, markdown)

    # 保护 $$ ... $$ (alternative display math)
    markdown = re.sub(r'\$\$[^$]+?\$\$', save_latex_block, markdown, flags=re.DOTALL)

    # 定义数学符号模式 - 排除占位符格式
    patterns = [
        # 希腊字母（小写和大写）- 但不在占位符中
        r'(?<!PLACEHOLDER)(?<!XYZ)\\?[αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ](?!PLACEHOLDER)',

        # LaTeX 希腊字母
        r'\\(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)',
        r'\\(Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)',

        # 数学字母类：\mathcal, \mathbb, \mathbf, \mathfrak, \mathsf
        r'\\(mathcal|mathbb|mathbf|mathfrak|mathsf|mathrm)\{[^}]+\}',

        # 下标模式：x_i, s_1, k_{i+1}, θ_j 等（至少一个字母后跟 _）
        r'[a-zA-Zα-ωΑ-Ω]_\{[^}]+\}',     # x_{i+1}
        r'[a-zA-Zα-ωΑ-Ω]_[a-zA-Z0-9]',    # s_i

        # 上标模式：x^2, θ^{*} 等
        r'[a-zA-Zα-ωΑ-Ω]\^\{[^}]+\}',     # x^{2n}
        r'[a-zA-Zα-ωΑ-Ω]\^[0-9+\-*]',     # x^2

        # 组合上下标：s_{i}^{j}, x_{i+1}^{*}
        r'[a-zA-Zα-ωΑ-Ω]_\{[^}]+\}\^\{[^}]+\}',
        r'[a-zA-Zα-ωΑ-Ω]\^[0-9+\-]_\{[^}]+\}',

        # LaTeX 数学符号/运算符
        r'\\(dots|ldots|cdots|vdots|ddots)',
        r'\\(le|ge|leq|geq|ne|neq|approx|equiv|sim)',
        r'\\(in|notin|subset|subseteq|supset|supseteq)',
        r'\\(cup|cap|setminus|times|div|pm|mp)',
        r'\\(to|rightarrow|leftarrow|leftrightarrow|Rightarrow|Leftarrow|Leftrightarrow)',
        r'\\(partial|nabla|infty|emptyset|exists|forall)',
        r'\\(lfloor|rfloor|lceil|rceil|langle|rangle)',
    ]

    # 对每个模式进行处理
    for pattern in patterns:
        def wrap_math(match):
            content = match.group(0)
            # 避免重复包裹
            if content.startswith('\\(') or content.startswith('$'):
                return content
            return f'\\( {content} \\)'

        markdown = re.sub(pattern, wrap_math, markdown)

    # 恢复之前保护的 LaTeX 块
    for i, block in enumerate(latex_blocks):
        markdown = markdown.replace(f"LATEXBLOCKPLACEHOLDERXYZ{i}PLACEHOLDERXYZ", block)

    return markdown

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

    # 1. 智能预处理 LaTeX 数学符号（在所有处理之前）
    markdown = preprocess_latex(markdown)

    # 2. 提取并渲染 Mermaid 图表
    mermaid_images = render_mermaid_diagrams(markdown)

    # 3. 替换 Markdown 中的 mermaid 代码块为图片引用
    markdown_with_images = replace_mermaid_with_images(markdown, mermaid_images)

    # 4. 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    docx_filename = f'output_{timestamp}_{uuid.uuid4().hex[:8]}.docx'
    docx_path = os.path.join(TEMP_DIR, docx_filename)

    # 5. Pandoc 转换
    convert_with_pandoc(markdown_with_images, docx_path)

    # 6. python-docx 样式调整
    adjust_docx_styles(docx_path)

    # 7. 生成预览 HTML
    preview_html = generate_preview_html(markdown_with_images)

    return {
        'html': preview_html,
        'docx_url': f'/api/download/{docx_filename}',
        'pdf_url': None  # PDF 导出为可选功能
    }

def generate_preview_html(markdown):
    """
    生成预览 HTML（保留 LaTeX 公式供 MathJax 渲染）

    Args:
        markdown: Markdown 内容

    Returns:
        str: HTML 内容
    """
    # 简单的 Markdown 转 HTML，保留 LaTeX 公式
    lines = markdown.split('\n')
    html_lines = []
    in_code_block = False
    code_lines = []

    for line in lines:
        # 检查代码块
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                # 代码块结束
                code_html = '<pre><code>' + '\n'.join(code_lines) + '</code></pre>'
                html_lines.append(code_html)
                in_code_block = False
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # 处理标题
        if line.startswith('# '):
            level = len(line) - len(line.lstrip('#'))
            if level <= 6:
                text = line.lstrip('#').strip()
                html_lines.append(f'<h{level}>{text}</h{level}>')
                continue

        # 处理粗体
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'_(.+?)_', r'<em>\1</em>', line)

        # 处理代码块
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        # 处理空行
        if not line.strip():
            html_lines.append('<br>')
        else:
            # 将 Markdown 格式的公式转换为 HTML（保留供 MathJax 处理）
            # \( ... \) 和 \[ ... \] 保持不变，让 MathJax 处理
            html_lines.append(f'<p>{line}</p>')

    html = '\n'.join(html_lines)

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
