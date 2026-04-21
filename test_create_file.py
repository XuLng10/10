import practice02.tools as tools

# 测试create_file函数
result = tools.create_file('.', '6.txt', '这是一个测试文件，包含100字左右的内容。这是一个测试文件，包含100字左右的内容。这是一个测试文件，包含100字左右的内容。这是一个测试文件，包含100字左右的内容。')
print(result)

# 检查文件是否存在
import os
if os.path.exists('6.txt'):
    print('文件已存在')
    with open('6.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        print('文件内容:', content)
else:
    print('文件不存在')
