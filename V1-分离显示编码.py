#!/usr/bin/env python3
"""
五笔码表HTML生成器
从txt格式的五笔码表生成完整的HTML页面
"""

import re
import sys
import os
from collections import defaultdict
import datetime

def parse_wubi_code_table(file_path):
    """
    解析五笔码表文件
    返回一个字典：{汉字: 编码}
    """
    wubi_map = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # 分割编码和汉字
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                    
                code = parts[0].strip().upper()
                # 处理可能有多个汉字的情况
                for char in parts[1:]:
                    char = char.strip()
                    if char and len(char) == 1:  # 只处理单字
                        # 如果同一个汉字有多个编码，取最短的
                        if char not in wubi_map or len(code) < len(wubi_map[char]):
                            wubi_map[char] = code
                            
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None
        
    return wubi_map

def generate_html(wubi_map, output_path):
    """
    生成HTML文件
    """
    # 将码表字典转换为JSON字符串
    wubi_json = "{\n"
    for i, (char, code) in enumerate(wubi_map.items()):
        wubi_json += f'    "{char}": "{code}"'
        if i < len(wubi_map) - 1:
            wubi_json += ",\n"
        else:
            wubi_json += "\n"
    wubi_json += "}"
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>五笔编码实时显示工具</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: "Microsoft YaHei", sans-serif;
        }}
        
        body {{
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }}
        
        h1 {{
            text-align: center;
            margin-bottom: 20px;
            color: #2c3e50;
        }}
        
        .description {{
            text-align: center;
            margin-bottom: 30px;
            color: #7f8c8d;
        }}
        
        .stats {{
            text-align: center;
            margin-bottom: 20px;
            color: #3498db;
            font-weight: bold;
        }}
        
        .input-section {{
            margin-bottom: 30px;
        }}
        
        .input-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }}
        
        #chinese-input {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        #chinese-input:focus {{
            border-color: #3498db;
            outline: none;
        }}
        
        .result-section {{
            margin-top: 30px;
        }}
        
        .result-label {{
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        
        #output-area {{
            min-height: 200px;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background-color: #f9f9f9;
            line-height: 2.5;
            font-size: 18px;
        }}
        
        .char-container {{
            display: inline-block;
            text-align: center;
            margin: 0 5px;
            vertical-align: top;
        }}
        
        .code {{
            font-size: 14px;
            color: #e74c3c;
            font-weight: bold;
            margin-bottom: 2px;
            background-color: #fff;
            padding: 2px 4px;
            border-radius: 3px;
            border: 1px solid #eee;
        }}
        
        .char {{
            font-size: 24px;
            margin-top: 2px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #95a5a6;
            font-size: 14px;
        }}
        
        .instructions {{
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-top: 20px;
            border-radius: 0 4px 4px 0;
        }}
        
        .instructions h3 {{
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        
        .instructions ul {{
            padding-left: 20px;
        }}
        
        .instructions li {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>五笔编码实时显示工具</h1>
        <p class="description">输入汉字，实时查看每个字对应的五笔编码</p>
        <div class="stats">码表包含 {len(wubi_map)} 个汉字</div>
        
        <div class="input-section">
            <label for="chinese-input" class="input-label">请输入汉字：</label>
            <input type="text" id="chinese-input" placeholder="在此输入汉字...">
        </div>
        
        <div class="result-section">
            <label class="result-label">编码显示：</label>
            <div id="output-area">
                输入汉字后，此处将显示每个字对应的五笔编码
            </div>
        </div>
        
        <div class="instructions">
            <h3>使用说明</h3>
            <ul>
                <li>在输入框中输入任意汉字，每个汉字上方会实时显示其五笔编码</li>
                <li>编码显示为大写字母</li>
                <li>如果某个汉字没有对应的编码，将显示为"---"</li>
                <li>当前码表包含 {len(wubi_map)} 个汉字</li>
            </ul>
        </div>
        
        <div class="footer">
            基于86五笔码表开发
        </div>
    </div>

    <script>
        // 五笔码表数据
        const wbCodeMap = {wubi_json};
        
        // 获取DOM元素
        const inputElement = document.getElementById('chinese-input');
        const outputElement = document.getElementById('output-area');
        
        // 输入事件处理
        inputElement.addEventListener('input', function() {{
            const inputText = this.value;
            updateOutput(inputText);
        }});
        
        // 更新输出区域
        function updateOutput(text) {{
            if (!text) {{
                outputElement.innerHTML = '输入汉字后，此处将显示每个字对应的五笔编码';
                return;
            }}
            
            let outputHTML = '';
            
            for (let i = 0; i < text.length; i++) {{
                const char = text[i];
                const code = wbCodeMap[char] || '---';
                
                outputHTML += `
                    <div class="char-container">
                        <div class="code">${{code}}</div>
                        <div class="char">${{char}}</div>
                    </div>
                `;
            }}
            
            outputElement.innerHTML = outputHTML;
        }}
        
        // 初始化示例
        updateOutput('五笔编码查询工具');
        inputElement.value = '五笔编码查询工具';
    </script>
</body>
</html>'''
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"成功生成HTML文件: {output_path}")
        return True
    except Exception as e:
        print(f"生成HTML文件时出错: {e}")
        return False

def main():
    
    input_file = 'wb86.txt'
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 默认输出文件名
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"index-V1.html"
    
    print(f"正在解析码表文件: {input_file}")
    wubi_map = parse_wubi_code_table(input_file)
    
    if wubi_map is None:
        print("解析码表失败，程序退出")
        return
    
    print(f"成功解析 {len(wubi_map)} 个汉字")
    
    print(f"正在生成HTML文件: {output_file}")
    if generate_html(wubi_map, output_file):
        print("生成完成！")
    else:
        print("生成失败")

if __name__ == "__main__":
    main()