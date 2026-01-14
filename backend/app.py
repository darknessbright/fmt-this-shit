# backend/app.py
from flask import Flask, send_file, request, jsonify, render_template_string
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')

@app.route('/')
def index():
    """返回主页面"""
    return send_file('../frontend/index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'pandoc_available': os.path.exists('../pandoc/pandoc.exe'),
        'mermaid_available': os.path.exists('../node_modules/.bin/mmdc.cmd')
    })

@app.route('/api/convert', methods=['POST'])
def convert():
    """转换接口 - 占位符"""
    data = request.json
    markdown = data.get('markdown', '')
    # TODO: 实现转换逻辑
    return jsonify({
        'html': '<p>预览功能开发中</p>',
        'docx_url': None,
        'pdf_url': None
    })

if __name__ == '__main__':
    print("=" * 40)
    print("  AI2Word 服务启动")
    print("  访问地址: http://localhost:5678")
    print("  按 Ctrl+C 停止服务")
    print("=" * 40)
    app.run(host='127.0.0.1', port=5678, debug=True)
