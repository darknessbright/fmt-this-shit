# backend/app.py
from flask import Flask, send_file, request, jsonify, render_template_string
from convert import convert_markdown, TEMP_DIR
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
    print("  AI2Word 服务启动")
    print("  访问地址: http://localhost:5678")
    print("  按 Ctrl+C 停止服务")
    print("=" * 40)
    app.run(host='127.0.0.1', port=5678, debug=True)
