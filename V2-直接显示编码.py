import json
import os

# 配置
INPUT_FILE = 'wb86.txt'
OUTPUT_FILE = 'index-V2.html'

# HTML 模板头部
HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>五笔86 - 完美输入体验版</title>
    <style>
        :root {
            --bg-color: #fdfbf7;
            --text-color: #333;
            --code-color: #e74c3c;
        }

        body {
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            background-color: #eef2f3;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }

        .paper {
            width: 100%;
            max-width: 900px;
            background: var(--bg-color);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-radius: 4px;
            padding: 40px 50px;
            box-sizing: border-box;
            min-height: 80vh;
        }

        h2 {
            text-align: center;
            color: #999;
            font-weight: 300;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            font-size: 26px;
            margin-top: 0;
        }

        /* 编辑器核心样式 */
        #editor {
            font-size: 36px;
            line-height: 3.2; /* 给编码留足空间 */
            color: var(--text-color);
            outline: none;
            white-space: pre-wrap;
            word-break: break-all;
            min-height: 60vh;
        }

        #editor:empty:before {
            content: "请直接输入... ";
            color: #ccc;
            font-size: 36px;
        }

        /* 五笔编码样式 */
        ruby {
            margin: 0 5px;
        }
        
        /* 关键：禁止用户编辑/选中 RT 里的内容，防止光标误入造成混乱 */
        rt {
            font-family: Consolas, monospace;
            font-size: 20px;
            color: var(--code-color);
            font-weight: bold;
            user-select: none; 
            -webkit-user-select: none;
            contenteditable: false; /* 核心修复：禁止光标进入编码区 */
            opacity: 0.8;
        }
    </style>
</head>
<body>

<div class="paper">
    <h2>五笔86 · 汉字反查编码</h2>
    <div id="editor" contenteditable="true" spellcheck="false"></div>
</div>

<script>
    // 1. 码表数据
    const wubiMap = 
"""

# HTML 模板尾部
HTML_TAIL = """;

    const editor = document.getElementById('editor');
    let isComposing = false;

    // 输入法状态监听
    editor.addEventListener('compositionstart', () => isComposing = true);
    editor.addEventListener('compositionend', () => {
        isComposing = false;
        updateEditor();
    });
    
    // 核心输入监听
    editor.addEventListener('input', (e) => {
        if (!isComposing) {
            updateEditor();
        }
    });

    function updateEditor() {
        // 1. 获取纯文本内容和光标相对于纯文本的位置
        // 这一步至关重要：必须忽略 <rt> 标签里的内容
        const { text, cursorIndex } = getTextAndCursor(editor);

        // 2. 如果内容没变（防止某些无效触发），或者是空的，简单处理
        if (text.length === 0) {
            editor.innerHTML = '';
            return;
        }

        // 3. 构建新的 HTML
        let newHtml = '';
        for (let char of text) {
            // 转义特殊字符，防止 < > & 破坏 HTML
            let safeChar = escapeHtml(char);

            if (char === '\\n') {
                newHtml += '<br>';
            } else if (wubiMap[char]) {
                // contenteditable="false" 确保光标无法在编码中停留
                newHtml += `<ruby>${safeChar}<rt contenteditable="false">${wubiMap[char].toUpperCase()}</rt></ruby>`;
            } else {
                newHtml += safeChar;
            }
        }

        // 4. 更新 DOM
        editor.innerHTML = newHtml;

        // 5. 恢复光标
        restoreCursor(editor, cursorIndex);
    }

    // --- 辅助工具函数 ---

    // HTML 转义，防止输入 <script> 等字符时出错
    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // 获取纯文本内容（跳过 rt 标签）以及光标位置
    function getTextAndCursor(root) {
        let text = '';
        let cursorIndex = 0;
        let foundCursor = false;
        
        const sel = window.getSelection();
        let anchorNode = sel.anchorNode;
        let anchorOffset = sel.anchorOffset;

        // 深度优先遍历 DOM
        function traverse(node) {
            // 如果是 RT 标签，直接忽略其内容
            if (node.nodeName === 'RT') return;

            if (node.nodeType === Node.TEXT_NODE) {
                const nodeText = node.nodeValue;
                
                // 检查光标是否在这个文本节点内
                if (!foundCursor && node === anchorNode) {
                    cursorIndex = text.length + anchorOffset;
                    foundCursor = true;
                }
                
                text += nodeText;
            } else if (node.nodeName === 'BR') {
                // BR 算一个换行符
                if (!foundCursor && node === anchorNode) {
                    // 光标在 BR 标签本身上（通常是空行）
                    cursorIndex = text.length; 
                    foundCursor = true;
                } else if (!foundCursor && Array.from(node.parentNode.childNodes).indexOf(node) + 1 === anchorOffset && node.parentNode === anchorNode) {
                     // 光标在 BR 之后
                     cursorIndex = text.length + 1;
                     foundCursor = true;
                }
                
                text += '\\n';
            } else {
                // 递归遍历子节点
                for (let i = 0; i < node.childNodes.length; i++) {
                    traverse(node.childNodes[i]);
                }
            }
        }

        traverse(root);
        
        // 如果遍历完了还没找到光标（比如在最后），设为最大长度
        if (!foundCursor) cursorIndex = text.length;

        return { text, cursorIndex };
    }

    // 恢复光标位置
    function restoreCursor(root, targetIndex) {
        let currentIndex = 0;
        const range = document.createRange();
        const sel = window.getSelection();
        let found = false;

        function traverse(node) {
            if (found) return;
            if (node.nodeName === 'RT') return; // 忽略 RT

            if (node.nodeType === Node.TEXT_NODE) {
                const len = node.nodeValue.length;
                if (targetIndex <= currentIndex + len) {
                    range.setStart(node, targetIndex - currentIndex);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    found = true;
                    return;
                }
                currentIndex += len;
            } else if (node.nodeName === 'BR') {
                if (targetIndex === currentIndex) {
                    range.setStartBefore(node);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    found = true;
                    return;
                }
                currentIndex += 1; 
            } else {
                for (let i = 0; i < node.childNodes.length; i++) {
                    traverse(node.childNodes[i]);
                }
            }
        }

        traverse(root);
        
        // 如果光标在最后
        if (!found) {
            range.selectNodeContents(root);
            range.collapse(false); // 到末尾
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }
    
    editor.focus();
</script>
</body>
</html>
"""

def process_wubi_table(filename):
    """读取码表，保留最短编码"""
    char_map = {}
    if not os.path.exists(filename):
        print(f"错误：找不到文件 {filename}")
        return None

    print(f"正在读取 {filename} ...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2: continue
                code, char = parts[0], parts[1]
                
                if char not in char_map:
                    char_map[char] = code
                else:
                    if len(code) < len(char_map[char]):
                        char_map[char] = code
    except Exception as e:
        print(f"读取错误: {e}")
        return None
    return char_map

def generate_html(data_map):
    print(f"正在生成 {OUTPUT_FILE} ...")
    json_data = json.dumps(data_map, ensure_ascii=False)
    full_content = HTML_HEAD + json_data + HTML_TAIL
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print("完成！请体验。")

if __name__ == "__main__":
    mapping = process_wubi_table(INPUT_FILE)
    if mapping:
        generate_html(mapping)