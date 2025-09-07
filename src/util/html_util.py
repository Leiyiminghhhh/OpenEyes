import os
import datetime
from collections import defaultdict


def generate_html_report(records, filename=None, summary: list=None):
    """
    对record的数组，根据time排序，按type分类，用表格展示所有字段，组建html，存储到logs/{today}目录
    content字段支持展开和收缩
    
    Args:
        records (list): Record对象列表
        filename (str): 保存的文件名，默认为report_{timestamp}.html
        summary (list): 摘要信息，在标题下方展示
    """
    # 按时间排序
    sorted_records = sorted(records, key=lambda x: x.time if x.time else datetime.datetime.min)
    
    # 按类型分类
    records_by_type = defaultdict(list)
    for record in sorted_records:
        records_by_type[record.type].append(record)
    
    # 生成HTML内容
    html_content = _build_html(records_by_type, summary)
    
    # 创建logs目录（如果不存在）
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    logs_dir = os.path.join("logs", today)
    os.makedirs(logs_dir, exist_ok=True)
    
    # 保存文件
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"
    
    file_path = os.path.join(logs_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return file_path


def _build_html(records_by_type, summary=None):
    """
    构建HTML内容
    
    Args:
        records_by_type (dict): 按类型分类的记录字典
        summary (list): 摘要信息数组
    """
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>记录报告</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            width: 100%;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            padding: 20px 0;
            margin: 0;
        }
        .summary {
            text-align: left;
            padding: 10px 20px;
            margin: 0 20px 20px 20px;
            background-color: #e9f7ef;
            border-left: 4px solid #4CAF50;
            font-size: 16px;
            line-height: 1.5;
        }
        .summary-item {
            margin: 5px 0;
        }
        .summary-index {
            font-weight: bold;
            margin-right: 10px;
        }
        .summary-key {
            font-weight: bold;
        }
        .type-section {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
            margin: 20px;
        }
        .type-header {
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            font-size: 1.2em;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .content-cell {
            max-width: 300px;
        }
        .content-wrapper {
            position: relative;
        }
        .short-content {
            display: inline;
        }
        .full-content {
            display: none;
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .toggle-btn {
            color: #1E90FF;
            cursor: pointer;
            font-weight: bold;
            margin-left: 10px;
            white-space: nowrap;
        }
        .toggle-btn:hover {
            text-decoration: underline;
        }
        .url-link {
            color: #1E90FF;
            text-decoration: none;
            white-space: nowrap;
        }
        .url-link:hover {
            text-decoration: underline;
        }
        .no-records {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>记录报告</h1>
        """
    
    # 添加摘要信息
    if summary:
        html += '<div class="summary">'
        # 逐行输出summary数组，左对齐并带序号
        for i, line in enumerate(summary, 1):
            # 使用：分割字符串，第一部分加粗显示
            if '：' in line:
                parts = line.split('：', 1)
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ""
                html += f'<div class="summary-item"><span class="summary-index">{i}.</span><span class="summary-key">{key}：</span>{value}</div>'
            else:
                html += f'<div class="summary-item"><span class="summary-index">{i}.</span>{line}</div>'
        html += '</div>'
    
    # 为每个类型生成表格
    for record_type, records in records_by_type.items():
        html += f"""
        <div class="type-section">
            <div class="type-header">{record_type or '未分类'}</div>
        """
        
        if not records:
            html += '<div class="no-records">该分类下暂无记录</div>'
        else:
            html += """
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>标题</th>
                        <th>来源</th>
                        <th>内容</th>
                        <th>标签</th>
                        <th>链接</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for record in records:
                # 处理内容的显示，截取前20个字符作为简要内容
                content = record.content or ""
                short_content = content[:20] + "..." if len(content) > 20 else content
                full_content = content if len(content) > 20 else ""
                
                # 处理URL
                url_link = f'<a href="{record.url}" class="url-link" target="_blank">查看</a>' if record.url else "无"
                
                html += f"""
                    <tr>
                        <td>{record.time.strftime('%Y-%m-%d') if record.time else 'N/A'}</td>
                        <td>{record.title or 'N/A'}</td>
                        <td>{record.source or 'N/A'}</td>
                        <td class="content-cell">
                            <div class="content-wrapper">
                                <span class="short-content">{short_content}</span>
                """
                
                if full_content:
                    # 生成唯一的ID用于展开/收缩
                    record_id = f"record_{record.id}"
                    html += f"""
                                <span class="toggle-btn" onclick="toggleContent('{record_id}')">[展开]</span>
                                <div id="{record_id}" class="full-content">{full_content}</div>
                    """
                
                html += f"""
                            </div>
                        </td>
                        <td>{record.tags or 'N/A'}</td>
                        <td>{url_link}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += """
        </div>
        """
    
    html += """
        <script>
            function toggleContent(id) {
                var fullContent = document.getElementById(id);
                var toggleBtn = fullContent.previousElementSibling;
                
                if (fullContent.style.display === "none" || fullContent.style.display === "") {
                    fullContent.style.display = "block";
                    toggleBtn.textContent = "[收起]";
                } else {
                    fullContent.style.display = "none";
                    toggleBtn.textContent = "[展开]";
                }
            }
        </script>
    </body>
</html>
    """
    
    return html