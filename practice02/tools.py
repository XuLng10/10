import os
import stat
import time
import urllib.request
import urllib.error
from typing import Dict, Any


def list_directory(directory: str) -> str:
    """
    列出指定目录下的所有文件和子目录，包括文件的基本属性和大小信息

    Args:
        directory: 要列出的目录路径

    Returns:
        目录内容的格式化字符串
    """
    try:
        if not os.path.isdir(directory):
            return f"错误: 路径 '{directory}' 不是一个有效的目录"

        entries = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)

            try:
                file_stat = os.stat(full_path)

                if os.path.isdir(full_path):
                    file_type = "目录"
                elif os.path.isfile(full_path):
                    file_type = "文件"
                else:
                    file_type = "其他"

                size = file_stat.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                modify_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime))
                permissions = stat.filemode(file_stat.st_mode)

                entries.append({
                    "name": entry,
                    "type": file_type,
                    "size": size_str,
                    "modify_time": modify_time,
                    "permissions": permissions
                })
            except Exception:
                entries.append({
                    "name": entry,
                    "type": "未知",
                    "size": "无法访问",
                    "modify_time": "无法访问",
                    "permissions": "无法访问"
                })

        entries.sort(key=lambda x: (x["type"], x["name"]))

        result = f"目录 '{directory}' 的内容:\n\n"
        result += f"{'文件名':<30} {'类型':<6} {'大小':<12} {'修改时间':<20} {'权限'}\n"
        result += "-" * 90 + "\n"

        for entry in entries:
            result += f"{entry['name']:<30} {entry['type']:<6} {entry['size']:<12} {entry['modify_time']:<20} {entry['permissions']}\n"

        return result

    except Exception as e:
        return f"列出目录失败: {str(e)}"


def rename_file(old_path: str, new_name: str) -> str:
    """
    修改指定目录下文件的名字

    Args:
        old_path: 原文件的完整路径
        new_name: 新的文件名（不含路径）

    Returns:
        操作结果消息
    """
    try:
        if not os.path.exists(old_path):
            return f"错误: 文件 '{old_path}' 不存在"

        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, new_name)

        if os.path.exists(new_path):
            return f"错误: 目标文件 '{new_path}' 已存在"

        os.rename(old_path, new_path)
        return f"成功: 文件已从 '{old_path}' 重命名为 '{new_path}'"

    except Exception as e:
        return f"重命名文件失败: {str(e)}"


def delete_file(file_path: str) -> str:
    """
    删除指定路径的文件

    Args:
        file_path: 要删除的文件路径

    Returns:
        操作结果消息
    """
    try:
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_path}' 不存在"

        if not os.path.isfile(file_path):
            return f"错误: '{file_path}' 不是一个文件"

        os.remove(file_path)
        return f"成功: 文件 '{file_path}' 已删除"

    except Exception as e:
        return f"删除文件失败: {str(e)}"


def create_file(directory: str, file_name: str, content: str, overwrite: bool = False) -> str:
    """
    在指定目录下创建新文件并写入内容

    Args:
        directory: 目标目录路径
        file_name: 新文件名
        content: 要写入的内容
        overwrite: 如果文件已存在，是否覆盖（默认False）

    Returns:
        操作结果消息
    """
    try:
        if not os.path.isdir(directory):
            return f"错误: 目录 '{directory}' 不存在"

        full_path = os.path.join(directory, file_name)

        if os.path.exists(full_path) and not overwrite:
            return f"错误: 文件 '{full_path}' 已存在，若需覆盖请设置 overwrite=True"

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        if overwrite and os.path.exists(full_path):
            return f"成功: 文件 '{full_path}' 已覆盖，写入了 {len(content)} 个字符"
        else:
            return f"成功: 文件 '{full_path}' 已创建，写入了 {len(content)} 个字符"

    except Exception as e:
        return f"创建文件失败: {str(e)}"


def read_file(file_path: str) -> str:
    """
    读取指定文件的内容

    Args:
        file_path: 要读取的文件路径

    Returns:
        文件内容或错误消息
    """
    try:
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_path}' 不存在"

        if not os.path.isfile(file_path):
            return f"错误: '{file_path}' 不是一个文件"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f"文件 '{file_path}' 的内容:\n\n{content}"

    except Exception as e:
        return f"读取文件失败: {str(e)}"


def fetch_url(url: str, timeout: int = 30) -> str:
    """
    通过HTTP/HTTPS访问网页并返回网页内容

    Args:
        url: 网页URL地址
        timeout: 请求超时时间（秒），默认30秒

    Returns:
        网页内容或错误消息
    """
    try:
        import re
        url_match = re.search(r'https?://[^\s`\'"<>]+', url)
        if url_match:
            url = url_match.group(0)
        url = url.strip().strip('`').strip('"').strip("'").strip('<>')

        while url.endswith('`') or url.endswith("'") or url.endswith('"'):
            url = url[:-1].strip()

        if not url.startswith(('http://', 'https://')):
            return f"错误: URL必须以http://或https://开头"

        from urllib.parse import urlparse, quote

        parsed = urlparse(url)

        query = parsed.query
        if 'wttr.in' in parsed.netloc and 'format=' not in query:
            separator = '&' if query else '?'
            query = f"{query}{separator}format=j1" if query else "format=j1"

        path = parsed.path

        if query:
            full_path = f"{path}?{query}"
        else:
            full_path = path

        try:
            full_path.encode('ascii')
            final_url = f"{parsed.scheme}://{parsed.netloc}{full_path}"
        except UnicodeEncodeError:
            encoded_path = quote(path, safe='/:?=&')
            if query:
                final_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}?{query}"
            else:
                final_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"

        req = urllib.request.Request(
            final_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='replace')
        except Exception as e:
            if 'SSL' in str(e) or 'TLS' in str(e):
                if final_url.startswith('https://'):
                    http_url = final_url.replace('https://', 'http://')
                    req = urllib.request.Request(
                        http_url,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        content = response.read().decode('utf-8', errors='replace')
                else:
                    raise e
            else:
                raise e

        content_length = len(content)
        if content_length > 5000:
            content = content[:5000] + f"\n\n... (内容过长，已截断至前5000字符，总长度: {content_length} 字符)"

        return f"成功获取网页内容:\n\n{content}"

    except urllib.error.URLError as e:
        return f"网络请求失败: {str(e)}"
    except Exception as e:
        return f"获取网页内容失败: {str(e)}"


def execute_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """
    执行工具调用

    Args:
        tool_name: 工具名称
        args: 工具参数字典

    Returns:
        工具执行结果
    """
    tools_map = {
        "list_directory": list_directory,
        "rename_file": rename_file,
        "delete_file": delete_file,
        "create_file": create_file,
        "read_file": read_file,
        "fetch_url": fetch_url
    }

    if tool_name not in tools_map:
        return f"错误: 未知的工具 '{tool_name}'"

    try:
        tool_func = tools_map[tool_name]
        result = tool_func(**args)
        return result
    except TypeError as e:
        return f"错误: 工具 '{tool_name}' 的参数不正确 - {str(e)}"
    except Exception as e:
        return f"工具执行失败: {str(e)}"
