import os
import json
import time
import http.client
import sys
import signal
from urllib.parse import urlparse
import tools

# 导入工具函数
list_files = tools.list_files
rename_file = tools.rename_file
delete_file = tools.delete_file
create_file = tools.create_file
read_file = tools.read_file
curl = tools.curl

# 读取.env文件
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        print("Please copy env.example to .env and fill in the correct values")
        return None
    
    env = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip().strip('"')
    return env

# 处理Ctrl+C退出
def signal_handler(sig, frame):
    print("\nExiting chat...")
    sys.exit(0)

# 构建系统提示词
def get_system_prompt():
    return """
You are an AI assistant with access to the following tools:

1. list_files(directory): Lists all files and directories in the specified directory, including their properties (size, modification time, etc.)
   - Parameters:
     - directory: str - The path to the directory
   - Returns: A string containing the list of files and their properties

2. rename_file(directory, old_name, new_name): Renames a file in the specified directory
   - Parameters:
     - directory: str - The path to the directory
     - old_name: str - The current name of the file
     - new_name: str - The new name for the file
   - Returns: A string indicating the success or failure of the operation

3. delete_file(directory, file_name): Deletes a file in the specified directory
   - Parameters:
     - directory: str - The path to the directory
     - file_name: str - The name of the file to delete
   - Returns: A string indicating the success or failure of the operation

4. create_file(directory, file_name, content): Creates a new file in the specified directory with the given content
   - Parameters:
     - directory: str - The path to the directory
     - file_name: str - The name of the file to create
     - content: str - The content to write to the file
   - Returns: A string indicating the success or failure of the operation

5. read_file(directory, file_name): Reads the content of a file in the specified directory
   - Parameters:
     - directory: str - The path to the directory
     - file_name: str - The name of the file to read
   - Returns: The content of the file as a string

6. curl(url): Accesses a web page and returns its content
   - Parameters:
     - url: str - The URL of the web page to access
   - Returns: The content of the web page as a string

When you need to use a tool, respond with a JSON object in the following format:
{"toolcall": {"name": "tool_name", "params": {"param1": "value1", "param2": "value2", ...}}}

For example, to list files in the current directory, respond with:
{"toolcall": {"name": "list_files", "params": {"directory": "."}}}

After receiving the tool response, you should summarize the result for the user in natural language.
"""

# 调用LLM
def call_llm(messages, env):
    # 解析URL
    parsed_url = urlparse(env['BASE_URL'])
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    
    # 根据协议选择连接类型
    if parsed_url.scheme == 'https':
        conn = http.client.HTTPSConnection(host)
    else:
        conn = http.client.HTTPConnection(host)
    
    # 构建请求数据
    data = {
        "model": env['MODEL'],
        "messages": messages,
        "temperature": float(env.get('TEMPERATURE', 0.7)),
        "max_tokens": int(env.get('MAX_TOKENS', 1000))
    }
    
    # 开始计时
    start_time = time.time()
    
    # 发送请求
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env['API_KEY']}"
        }
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        conn.close()
        
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 解析响应
        response_json = json.loads(response_data)
        if 'error' in response_json:
            print(f"Error: {response_json['error']['message']}")
            return "", {}, elapsed_time
        
        # 提取响应内容和token使用情况
        response_content = response_json['choices'][0]['message']['content'].strip()
        usage = response_json.get('usage', {})
        
        return response_content, usage, elapsed_time
        
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return "", {}, 0

# 执行工具调用
def execute_tool_call(tool_call):
    tool_name = tool_call.get('name')
    params = tool_call.get('params', {})
    
    if tool_name == 'list_files':
        directory = params.get('directory')
        return list_files(directory)
    elif tool_name == 'rename_file':
        directory = params.get('directory')
        old_name = params.get('old_name')
        new_name = params.get('new_name')
        return rename_file(directory, old_name, new_name)
    elif tool_name == 'delete_file':
        directory = params.get('directory')
        file_name = params.get('file_name')
        return delete_file(directory, file_name)
    elif tool_name == 'create_file':
        directory = params.get('directory')
        file_name = params.get('file_name')
        content = params.get('content')
        return create_file(directory, file_name, content)
    elif tool_name == 'read_file':
        directory = params.get('directory')
        file_name = params.get('file_name')
        return read_file(directory, file_name)
    elif tool_name == 'curl':
        url = params.get('url')
        return curl(url)
    else:
        return f"Error: Unknown tool '{tool_name}'"

# 主聊天循环
def chat_loop():
    env = load_env()
    if not env:
        return
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 初始化聊天历史
    messages = [
        {"role": "system", "content": get_system_prompt()}
    ]
    
    print("=== Tool Calling Chat with LLM ===")
    print("Type your message and press Enter")
    print("Press Ctrl+C to exit")
    print()
    print("Available tools:")
    print("1. list_files - List files in a directory")
    print("2. rename_file - Rename a file")
    print("3. delete_file - Delete a file")
    print("4. create_file - Create a new file with content")
    print("5. read_file - Read content of a file")
    print("6. curl - Access web page content")
    print()
    
    while True:
        try:
            # 获取用户输入
            user_input = input("You: ")
            if not user_input.strip():
                continue
            
            # 添加用户消息到历史
            messages.append({"role": "user", "content": user_input})
            
            # 调用LLM并获取响应
            response_content, usage, elapsed_time = call_llm(messages, env)
            
            # 检查是否是工具调用
            try:
                # 尝试从markdown代码块中提取JSON
                json_content = response_content
                import re
                # 尝试匹配各种格式的代码块
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_content)
                if json_match:
                    json_content = json_match.group(1).strip()
                
                # 也尝试直接匹配JSON对象
                if not json_content.strip().startswith('{'):
                    # 尝试找到JSON对象的开始和结束
                    json_start = response_content.find('{')
                    json_end = response_content.rfind('}')
                    if json_start != -1 and json_end != -1:
                        json_content = response_content[json_start:json_end+1]
                
                response_json = json.loads(json_content)
                if 'toolcall' in response_json:
                    tool_call = response_json['toolcall']
                    print(f"Assistant: Calling tool '{tool_call['name']}'...")
                    
                    # 执行工具调用
                    tool_result = execute_tool_call(tool_call)
                    print(f"Tool result: {tool_result}")
                    
                    # 添加工具调用和结果到历史
                    messages.append({"role": "assistant", "content": response_content})
                    messages.append({"role": "user", "content": f"Tool response: {tool_result}"})
                    
                    # 再次调用LLM获取总结
                    summary, _, _ = call_llm(messages, env)
                    print(f"Assistant: {summary}")
                    messages.append({"role": "assistant", "content": summary})
                else:
                    print(f"Assistant: {response_content}")
                    messages.append({"role": "assistant", "content": response_content})
            except json.JSONDecodeError:
                # 不是工具调用，直接显示响应
                print(f"Assistant: {response_content}")
                messages.append({"role": "assistant", "content": response_content})
            
            # 打印性能信息
            if usage:
                total_tokens = usage.get('total_tokens', 0)
                print(f"\n=== Performance ===")
                print(f"Time taken: {elapsed_time:.2f} seconds")
                print(f"Tokens used: {total_tokens}")
                if elapsed_time > 0:
                    print(f"Tokens per second: {total_tokens / elapsed_time:.2f}")
                print()
            
        except KeyboardInterrupt:
            print("\nExiting chat...")
            break

if __name__ == "__main__":
    chat_loop()
