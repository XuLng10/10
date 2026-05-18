import os
import json
import time
import sys
import select
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


def call_llm_streaming(base_url: str, model: str, api_key: str, 
                       messages: list, timeout: int = 60) -> str:
    """
    使用Python标准库进行流式LLM API调用
    返回完整的响应内容（流式输出过程中会逐字打印）
    """
    protocol, host, base_path = parse_url(base_url)
    endpoint = f"{base_path}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }
    
    if protocol == 'https':
        import http.client
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        import http.client
        conn = http.client.HTTPConnection(host, timeout=timeout)
    
    full_response = ""
    
    try:
        conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        
        if response.status != 200:
            response_data = response.read().decode('utf-8')
            raise Exception(f"API请求失败: {response.status} - {response_data}")
        
        buffer = ""
        while True:
            chunk = response.read(1024)
            if not chunk:
                break
            
            buffer += chunk.decode('utf-8')
            
            while '\n\n' in buffer:
                event_str, buffer = buffer.split('\n\n', 1)
                
                if event_str.startswith('data: '):
                    data_str = event_str[6:]
                    if data_str == '[DONE]':
                        return full_response
                    
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                full_response += content
                    except json.JSONDecodeError:
                        continue
        
        return full_response
    finally:
        conn.close()


def get_user_input(prompt: str = "你: ") -> str:
    """
    从终端获取用户输入
    """
    try:
        # 尝试使用select方式（Unix-like系统）
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
        input_chars = []
        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == '\n':
                    break
                elif char == '\x7f':  # Backspace
                    if input_chars:
                        input_chars.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ord(char) == 27:  # Escape sequence
                    # 忽略箭头键等特殊字符
                    sys.stdin.read(2)
                else:
                    input_chars.append(char)
                    sys.stdout.write(char)
                    sys.stdout.flush()
        
        return ''.join(input_chars)
    except OSError:
        # Windows系统上select.select与stdin不兼容，使用简单的input()
        return input()


def main():
    """
    主函数：终端聊天界面
    """
    print("=" * 60)
    print("AI智能体终端聊天")
    print("=" * 60)
    print("提示: 输入消息后按回车发送，按 Ctrl+C 退出")
    print("=" * 60)
    
    try:
        env_vars = load_env_file()
        
        base_url = env_vars.get('LLM_BASE_URL')
        model = env_vars.get('LLM_MODEL')
        api_key = env_vars.get('LLM_API_KEY')
        timeout = int(env_vars.get('LLM_TIMEOUT', '60'))
        
        if not all([base_url, model, api_key]):
            raise ValueError("缺少必要的环境变量配置")
        
        print(f"\n已连接到: {base_url}")
        print(f"使用模型: {model}\n")
        
        # 初始化历史聊天记录
        history: List[Dict[str, str]] = []
        
        while True:
            try:
                # 获取用户输入
                user_input = get_user_input("你: ")
                if not user_input.strip():
                    continue
                
                # 添加用户消息到历史
                history.append({"role": "user", "content": user_input})
                
                # 构建请求消息（只保留最近的对话以控制上下文长度）
                messages = history.copy()
                
                # 发送请求并流式输出响应
                print("AI: ", end='', flush=True)
                start_time = time.time()
                response_content = call_llm_streaming(base_url, model, api_key, messages, timeout)
                end_time = time.time()
                print()  # 换行
                
                # 添加AI响应到历史
                history.append({"role": "assistant", "content": response_content})
                
                # 统计信息
                print(f"\n[耗时: {round(end_time - start_time, 2)}秒]")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n感谢使用！再见！")
                break
            
            except Exception as e:
                print(f"\n错误: {e}")
                # 如果发生错误，移除当前用户消息以保持历史一致性
                if history and history[-1]['role'] == 'user':
                    history.pop()
                continue
        
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("请按照以下步骤操作:")
        print("1. 复制 env.example 文件为 .env")
        print("2. 在 .env 文件中填入正确的LLM配置信息")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()