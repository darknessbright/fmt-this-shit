"""测试用户提到的复杂inline math"""
import sys
import urllib.request
import json

sys.path.insert(0, r'E:\ModelObjects\AI2Word')

# 用户提到的复杂inline math
test = r'''
设真实标签序列为 \( \mathbf{y} = \{y_1, y_2, \dots, y_N\} \)，预测标签序列为 \( \mathbf{\hat{y}} = \{\hat{y}_1, \hat{y}_2, \dots, \hat{y}_N\} \)，其中 \( y_i, \hat{y}_i \in \{0, 1\} \) 分别表示
'''

print('测试复杂inline math...')
print('原始文本:')
print(test)
print()

# 调用API
req = urllib.request.Request(
    'http://127.0.0.1:5678/api/convert',
    data=json.dumps({'markdown': test}).encode('utf-8'),
    headers={'Content-Type': 'application/json; charset=utf-8'}
)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))

import html as html_module
decoded_html = html_module.unescape(data['html'])

print('生成的HTML:')
print(decoded_html[:500])
print()

# 检查LaTeX格式
import re
# 查找所有 \( ... \) 模式
inline_pattern = r'\\\(.*?\\\)'
matches = re.findall(inline_pattern, decoded_html)
print(f'找到 {len(matches)} 个inline math标记')
for i, match in enumerate(matches):
    print(f'{i}: {repr(match[:80])}...')
