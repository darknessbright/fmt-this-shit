# backend/app.py
from flask import Flask, send_file, request, jsonify, render_template_string
from convert import convert_markdown, TEMP_DIR, PANDOC_PATH, MMDC_PATH, PROJECT_ROOT
import os
import sys

# 支持 PyInstaller 打包后的资源路径
if getattr(sys, 'frozen', False):
    # 打包环境：frontend 在 _MEIPASS 内
    template_folder = os.path.join(sys._MEIPASS, 'frontend')
    static_folder = os.path.join(sys._MEIPASS, 'frontend')
else:
    # 开发环境
    template_folder = '../frontend'
    static_folder = '../frontend'

app = Flask(__name__, static_folder=static_folder, static_url_path='')

@app.route('/')
def index():
    """返回主页面"""
    if getattr(sys, 'frozen', False):
        # 打包环境
        index_path = os.path.join(sys._MEIPASS, 'frontend', 'index.html')
    else:
        # 开发环境
        index_path = os.path.join(PROJECT_ROOT, 'frontend', 'index.html')
    return send_file(index_path)

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'pandoc_available': os.path.exists(PANDOC_PATH),
        'mermaid_available': os.path.exists(MMDC_PATH)
    })

@app.route('/api/convert', methods=['POST'])
def convert():
    """转换接口"""
    data = request.json
    markdown = data.get('markdown', '')

    if not markdown.strip():
        return jsonify({'error': '内容不能为空'}), 400

    try:
        result = convert_markdown(markdown)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download(filename):
    """文件下载"""
    file_path = os.path.join(TEMP_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    print("=" * 40)
    print("  Fmt this Shit 服务启动")
    print("  访问地址: http://localhost:5678")
    print("  按 Ctrl+C 停止服务")
    print("=" * 40)
    app.run(host='127.0.0.1', port=5678, debug=True)
