import os
import stat
import time
from typing import List, Dict, Any


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
            
            # 获取文件属性
            try:
                file_stat = os.stat(full_path)
                
                # 文件类型
                if os.path.isdir(full_path):
                    file_type = "目录"
                elif os.path.isfile(full_path):
                    file_type = "文件"
                else:
                    file_type = "其他"
                
                # 文件大小（转换为可读格式）
                size = file_stat.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                
                # 修改时间
                modify_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime))
                
                # 权限信息
                permissions = stat.filemode(file_stat.st_mode)
                
                entries.append({
                    "name": entry,
                    "type": file_type,
                    "size": size_str,
                    "modify_time": modify_time,
                    "permissions": permissions
                })
            except Exception as e:
                entries.append({
                    "name": entry,
                    "type": "未知",
                    "size": "无法访问",
                    "modify_time": "无法访问",
                    "permissions": "无法访问"
                })
        
        # 按类型排序（目录优先），然后按名称排序
        entries.sort(key=lambda x: (x["type"], x["name"]))
        
        # 格式化输出
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


# 工具函数映射表
tools_map = {
    "list_directory": list_directory,
    "rename_file": rename_file,
    "delete_file": delete_file,
    "create_file": create_file,
    "read_file": read_file
}


def get_tools_description() -> str:
    """
    获取所有工具的描述信息，用于系统提示词
    """
    return """你是一个具备文件操作能力的AI助手，可以调用以下工具来完成任务：

可用工具列表：

1. list_directory(directory: str)
   - 功能：列出指定目录下的所有文件和子目录
   - 参数：directory - 目录路径（字符串）
   - 返回：目录内容的详细信息，包括文件名、类型、大小、修改时间和权限

2. rename_file(old_path: str, new_name: str)
   - 功能：修改指定文件的名称
   - 参数：
     - old_path - 原文件的完整路径（字符串）
     - new_name - 新的文件名（不含路径，字符串）
   - 返回：操作结果消息

3. delete_file(file_path: str)
   - 功能：删除指定的文件
   - 参数：file_path - 要删除的文件路径（字符串）
   - 返回：操作结果消息

4. create_file(directory: str, file_name: str, content: str, overwrite: bool = False)
   - 功能：在指定目录下创建新文件并写入内容
   - 参数：
     - directory - 目标目录路径（字符串）
     - file_name - 新文件名（字符串）
     - content - 要写入的内容（字符串）
     - overwrite - 如果文件已存在，是否覆盖（布尔值，默认False）
   - 返回：操作结果消息

5. read_file(file_path: str)
   - 功能：读取指定文件的内容
   - 参数：file_path - 要读取的文件路径（字符串）
   - 返回：文件内容或错误消息

调用格式：
当你需要调用工具时，请使用JSON格式输出，例如：
{"tool": "工具名称", "args": {"参数名": "参数值", ...}}

注意事项：
- 请确保路径参数使用正确的格式
- 在执行删除操作前，请确认文件路径正确
- 创建文件时，内容参数可以包含换行符"""


def parse_tool_call(response: str) -> Dict[str, Any]:
    """
    解析LLM响应中的工具调用
    
    Args:
        response: LLM的响应内容
        
    Returns:
        包含工具名称和参数的字典，如果解析失败返回None
    """
    try:
        # 尝试从响应中提取JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            parsed = json.loads(json_str)
            
            if "tool" in parsed and "args" in parsed:
                return parsed
    except Exception:
        pass
    
    return None


def execute_tool_call(tool_call: Dict[str, Any]) -> str:
    """
    执行工具调用
    
    Args:
        tool_call: 包含工具名称和参数的字典
        
    Returns:
        工具执行结果
    """
    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})
    
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

# 为了兼容性，导入json模块
import json