// frontend/js/app.js

// 初始化 CodeMirror 编辑器
const editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
    mode: 'markdown',
    lineNumbers: true,
    lineWrapping: true,
    theme: 'default'
});

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// 当前转换状态
let currentDocxUrl = null;
let currentPdfUrl = null;
let isConverting = false;

// 转换 Markdown
async function convertMarkdown() {
    const markdown = editor.getValue();

    if (!markdown.trim()) {
        document.getElementById('preview').innerHTML =
            '<p class="placeholder">在左侧输入 Markdown 内容，这里将显示预览...</p>';
        currentDocxUrl = null;
        currentPdfUrl = null;
        return;
    }

    if (isConverting) return;

    isConverting = true;
    const preview = document.getElementById('preview');
    preview.innerHTML = '<p class="loading">转换中</p>';

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ markdown })
        });

        if (!response.ok) {
            throw new Error('转换失败');
        }

        const data = await response.json();

        // 更新预览
        preview.innerHTML = data.html;

        // 保存下载链接
        currentDocxUrl = data.docx_url;
        currentPdfUrl = data.pdf_url;

    } catch (error) {
        preview.innerHTML = `<p style="color: red;">转换失败: ${error.message}</p>`;
    } finally {
        isConverting = false;
    }
}

// 防抖的转换函数
const debouncedConvert = debounce(convertMarkdown, 500);

// 监听编辑器变化
editor.on('change', debouncedConvert);

// 导出 Word
document.getElementById('exportWord').addEventListener('click', async () => {
    if (!currentDocxUrl) {
        alert('请先输入内容并等待转换完成');
        return;
    }

    // 触发下载
    const link = document.createElement('a');
    link.href = currentDocxUrl;
    link.download = `document_${Date.now()}.docx`;
    link.click();
});

// 导出 PDF
document.getElementById('exportPdf').addEventListener('click', () => {
    alert('PDF 导出功能开发中，请使用 Word 导出后手动转换');
});

// 初始化示例内容
const exampleMarkdown = `# 欢迎使用 AI2Word

这是一个 Markdown 转 Word 的工具。

## 支持的功能

- **粗体** 和 *斜体*
- 数学公式: $E=mc^2$
- 代码块
- 表格

## 示例代码

\`\`\`python
def hello():
    print("Hello, World!")
\`\`\`

开始输入你的内容吧！
`;

editor.setValue(exampleMarkdown);
