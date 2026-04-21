import os
import time

# 1. 列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）
def list_files(directory):
    """
    列出指定目录下的所有文件及其基本属性
    
    Args:
        directory (str): 目录路径
    
    Returns:
        str: 包含文件列表和属性的字符串
    """
    try:
        if not os.path.exists(directory):
            return f"错误: 目录 '{directory}' 不存在"
        
        if not os.path.isdir(directory):
            return f"错误: '{directory}' 不是一个目录"
        
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                mtime = os.path.getmtime(item_path)
                mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                files.append(f"文件: {item} | 大小: {size} 字节 | 修改时间: {mtime_str}")
            elif os.path.isdir(item_path):
                files.append(f"目录: {item}")
        
        if not files:
            return f"目录 '{directory}' 为空"
        
        return "\n".join(files)
    except Exception as e:
        return f"错误: {str(e)}"

# 2. 修改某个目录下某个文件的名字
def rename_file(directory, old_name, new_name):
    """
    修改指定目录下的文件名称
    
    Args:
        directory (str): 目录路径
        old_name (str): 旧文件名
        new_name (str): 新文件名
    
    Returns:
        str: 操作结果
    """
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        
        if not os.path.exists(old_path):
            return f"错误: 文件 '{old_name}' 不存在"
        
        if os.path.exists(new_path):
            return f"错误: 文件 '{new_name}' 已存在"
        
        os.rename(old_path, new_path)
        return f"成功: 文件已从 '{old_name}' 重命名为 '{new_name}'"
    except Exception as e:
        return f"错误: {str(e)}"

# 3. 删除某个目录下的某个文件
def delete_file(directory, file_name):
    """
    删除指定目录下的文件
    
    Args:
        directory (str): 目录路径
        file_name (str): 文件名
    
    Returns:
        str: 操作结果
    """
    try:
        file_path = os.path.join(directory, file_name)
        
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_name}' 不存在"
        
        if not os.path.isfile(file_path):
            return f"错误: '{file_name}' 不是一个文件"
        
        os.remove(file_path)
        return f"成功: 文件 '{file_name}' 已删除"
    except Exception as e:
        return f"错误: {str(e)}"

# 4. 在某个目录下新建1个文件，并且写入内容
def create_file(directory, file_name, content):
    """
    在指定目录下创建新文件并写入内容
    
    Args:
        directory (str): 目录路径
        file_name (str): 文件名
        content (str): 文件内容
    
    Returns:
        str: 操作结果
    """
    try:
        if not os.path.exists(directory):
            return f"错误: 目录 '{directory}' 不存在"
        
        if not os.path.isdir(directory):
            return f"错误: '{directory}' 不是一个目录"
        
        file_path = os.path.join(directory, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if os.path.exists(file_path):
            return f"成功: 文件 '{file_name}' 已更新并写入内容"
        else:
            return f"成功: 文件 '{file_name}' 已创建并写入内容"
    except Exception as e:
        return f"错误: {str(e)}"

# 5. 读取某个目录下的某个文件的内容
def read_file(directory, file_name):
    """
    读取指定目录下的文件内容
    
    Args:
        directory (str): 目录路径
        file_name (str): 文件名
    
    Returns:
        str: 文件内容或错误信息
    """
    try:
        file_path = os.path.join(directory, file_name)
        
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_name}' 不存在"
        
        if not os.path.isfile(file_path):
            return f"错误: '{file_name}' 不是一个文件"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"错误: {str(e)}"

# 6. 通过curl访问网页并返回网页内容
def curl(url):
    """
    通过网络访问指定URL并返回网页内容
    
    Args:
        url (str): 要访问的网页URL
    
    Returns:
        str: 网页内容或错误信息
    """
    try:
        import urllib.request
        import urllib.error
        import urllib.parse
        
        # 对URL进行编码处理，确保中文字符能正确处理
        parsed_url = urllib.parse.urlparse(url)
        encoded_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            urllib.parse.quote(parsed_url.path),
            parsed_url.params,
            urllib.parse.quote(parsed_url.query),
            parsed_url.fragment
        ))
        
        # 发送HTTP请求
        with urllib.request.urlopen(encoded_url, timeout=10) as response:
            # 读取响应内容
            content = response.read().decode('utf-8', errors='replace')
            # 限制返回内容长度，避免过大
            if len(content) > 10000:
                content = content[:10000] + "\n... (内容过长，已截断)"
            return content
    except urllib.error.URLError as e:
        return f"错误: 网络请求失败 - {str(e)}"
    except Exception as e:
        return f"错误: {str(e)}"
