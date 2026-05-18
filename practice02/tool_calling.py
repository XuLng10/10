import os
import json
import time
import http.client
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """
    手动解析.env文件
    """
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    else:
        raise FileNotFoundError(f"环境文件 {env_path} 不存在，请从env.example复制并配置")
    return env_vars


def parse_url(base_url: str) -> Tuple[str, str, str]:
    """
    解析URL，返回(protocol, host, path)
    """
    parsed = urlparse(base_url)
    return parsed.scheme, parsed.netloc, parsed.path.rstrip('/') or ''


def call_llm_api(base_url: str, model: str, api_key: str, 
                 messages: list, timeout: int = 60) -> Dict[str, Any]:
    """
    使用Python标准库http.client调用OpenAI兼容的LLM API
    支持HTTP和HTTPS协议自动切换
    """
    protocol, host, base_path = parse_url(base_url)
    endpoint = f"{base_path}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    if protocol == 'https':
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)
    
    try:
        conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        
        if response.status != 200:
            raise Exception(f"API请求失败: {response.status} - {response_data}")
        
        return json.loads(response_data)
    finally:
        conn.close()


def get_system_prompt() -> str:
    """
    获取工具调用系统提示词
    """
    return """你是一个具备文件操作能力的AI助手，可以调用以下工具来完成任务：

可用工具列表：

1. list_directory(directory: str)
   - 功能：列出指定目录下的所有文件和子目录
   - 参数：directory - 目录路径（字符串）
   - 返回：目录内容的详细信息

2. rename_file(old_path: str, new_name: str)
   - 功能：修改指定文件的名称
   - 参数：
     - old_path - 原文件的完整路径（字符串）
     - new_name - 新的文件名（不含路径，字符串）

3. delete_file(file_path: str)
   - 功能：删除指定的文件
   - 参数：file_path - 要删除的文件路径（字符串）

4. create_file(directory: str, file_name: str, content: str, overwrite: bool = False)
   - 功能：在指定目录下创建新文件并写入内容
   - 参数：
     - directory - 目标目录路径（字符串）
     - file_name - 新文件名（字符串）
     - content - 要写入的内容（字符串）
     - overwrite - 如果文件已存在，是否覆盖（布尔值，默认False）

5. read_file(file_path: str)
   - 功能：读取指定文件的内容
   - 参数：file_path - 要读取的文件路径（字符串）

## 调用格式

当你需要调用工具时，请使用JSON格式输出，格式如下：
{"tool": "工具名称", "args": {"参数名": "参数值", ...}}

## 注意事项

- 如果你需要调用工具来完成用户的请求，请输出JSON格式的工具调用
- 如果不需要调用工具，可以直接回答用户
- **重要：严格按照用户指定的文件名进行操作，不要随意添加或修改文件名**
  - 例如：用户说"将1.txt改为6.txt"，应该使用"1.txt"而不是"file1.txt"
  - 例如：用户说"读取test.txt"，应该使用"test.txt"而不是"file_test.txt"
- 在执行文件操作前，建议先使用list_directory工具确认文件是否存在
- 请确保路径参数使用正确的格式（例如：Windows使用反斜杠，Linux/macOS使用正斜杠）
- 在执行删除操作前，请确认文件路径正确
- 工具执行完成后，我会将结果返回给你，你需要根据结果进行总结回答

请记住你的角色是帮助用户完成任务，合理使用工具！"""


def parse_tool_call(response: str) -> Dict[str, Any]:
    """
    解析LLM响应中的工具调用
    
    Args:
        response: LLM的响应内容
        
    Returns:
        包含工具名称和参数的字典，如果解析失败返回None
    """
    try:
        # 先尝试从```json块中提取
        json_start = response.find("```json")
        if json_start != -1:
            json_end = response.find("```", json_start + 7)
            if json_end != -1:
                json_str = response[json_start + 7:json_end].strip()
                parsed = json.loads(json_str)
                if "tool" in parsed and "args" in parsed:
                    return parsed
        
        # 如果没有```json块，尝试直接查找JSON
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


def execute_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """
    执行工具调用
    """
    # 导入工具函数
    from tools import list_directory, rename_file, delete_file, create_file, read_file
    
    tools_map = {
        "list_directory": list_directory,
        "rename_file": rename_file,
        "delete_file": delete_file,
        "create_file": create_file,
        "read_file": read_file
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


def main():
    """
    主函数：工具调用演示
    """
    print("=" * 60)
    print("AI智能体工具调用演示")
    print("=" * 60)
    
    try:
        env_vars = load_env_file()
        
        base_url = env_vars.get('LLM_BASE_URL')
        model = env_vars.get('LLM_MODEL')
        api_key = env_vars.get('LLM_API_KEY')
        timeout = int(env_vars.get('LLM_TIMEOUT', '60'))
        
        if not all([base_url, model, api_key]):
            raise ValueError("缺少必要的环境变量配置")
        
        print(f"\n配置信息:")
        print(f"  Base URL: {base_url}")
        print(f"  Model: {model}")
        print(f"  Timeout: {timeout}s")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n你: ")
                if not user_input.strip():
                    continue
                
                if user_input.lower() == 'exit':
                    print("再见！")
                    break
                
                # 构建消息列表
                messages = [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": user_input}
                ]
                
                print("\nAI: 思考中...")
                
                # 调用LLM
                start_time = time.time()
                response = call_llm_api(base_url, model, api_key, messages, timeout)
                end_time = time.time()
                
                ai_response = response['choices'][0]['message']['content']
                
                # 检查是否包含工具调用
                tool_call = parse_tool_call(ai_response)
                
                if tool_call:
                    print(f"AI: 正在调用工具...")
                    print(f"  工具: {tool_call['tool']}")
                    print(f"  参数: {json.dumps(tool_call['args'], ensure_ascii=False)}")
                    
                    # 执行工具
                    tool_result = execute_tool(tool_call['tool'], tool_call['args'])
                    print(f"\n工具执行结果:\n{tool_result}")
                    
                    # 检查是否是create_file工具的"文件已存在"错误，如果是，自动重试并设置overwrite=True
                    if tool_call['tool'] == 'create_file' and "已存在" in tool_result and "overwrite=True" in tool_result:
                        print("\nAI: 检测到文件已存在，自动尝试覆盖...")
                        tool_call['args']['overwrite'] = True
                        print(f"  工具: {tool_call['tool']}")
                        print(f"  参数: {json.dumps(tool_call['args'], ensure_ascii=False)}")
                        
                        tool_result = execute_tool(tool_call['tool'], tool_call['args'])
                        print(f"\n工具执行结果:\n{tool_result}")
                    
                    # 将工具结果返回给LLM进行总结
                    messages.append({"role": "assistant", "content": ai_response})
                    messages.append({"role": "user", "content": f"工具执行结果:\n{tool_result}\n\n请总结这个结果。"})
                    
                    summary_response = call_llm_api(base_url, model, api_key, messages, timeout)
                    summary = summary_response['choices'][0]['message']['content']
                    print(f"\nAI: {summary}")
                else:
                    print(f"AI: {ai_response}")
                
                print(f"\n[耗时: {round(end_time - start_time, 2)}秒]")
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}")
        
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("请按照以下步骤操作:")
        print("1. 复制 env.example 文件为 .env")
        print("2. 在 .env 文件中填入正确的LLM配置信息")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()