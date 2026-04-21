import os
import json
import time
import http.client
import sys
import signal
from urllib.parse import urlparse

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

# 流式调用LLM
def call_llm_stream(messages, env):
    # 解析URL
    parsed_url = urlparse(env['BASE_URL'])
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    
    # 构建请求数据
    data = {
        "model": env['MODEL'],
        "messages": messages,
        "temperature": float(env.get('TEMPERATURE', 0.7)),
        "max_tokens": int(env.get('MAX_TOKENS', 1000)),
        "stream": True
    }
    
    # 开始计时
    start_time = time.time()
    
    # 发送请求
    try:
        conn = http.client.HTTPSConnection(host)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env['API_KEY']}"
        }
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()
        
        # 处理流式响应
        response_content = ""
        usage = {}
        
        print("Assistant:", end=" ", flush=True)
        
        for line in response:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                data_part = line[6:]
                if data_part == '[DONE]':
                    break
                try:
                    chunk = json.loads(data_part)
                    if 'choices' in chunk:
                        choice = chunk['choices'][0]
                        if 'delta' in choice:
                            delta = choice['delta']
                            if 'content' in delta:
                                content = delta['content']
                                print(content, end="", flush=True)
                                response_content += content
                    if 'usage' in chunk:
                        usage = chunk['usage']
                except json.JSONDecodeError:
                    pass
        
        print()  # 换行
        conn.close()
        
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 提取token使用情况
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # 计算速度
        if elapsed_time > 0:
            tokens_per_second = total_tokens / elapsed_time
        else:
            tokens_per_second = 0
        
        # 打印性能信息
        print(f"\n=== Performance ===")
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print(f"Tokens used: {total_tokens}")
        print(f"Tokens per second: {tokens_per_second:.2f}")
        print()
        
        return response_content, usage
        
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return "", {}

# 主聊天循环
def chat_loop():
    env = load_env()
    if not env:
        return
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 初始化聊天历史
    messages = []
    
    print("=== Terminal Chat with LLM ===")
    print("Type your message and press Enter")
    print("Press Ctrl+C to exit")
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
            assistant_response, usage = call_llm_stream(messages, env)
            
            # 添加助手响应到历史
            messages.append({"role": "assistant", "content": assistant_response})
            
            # 可选：限制历史记录长度，避免token消耗过大
            # if len(messages) > 10:  # 保留最近10条消息
            #     messages = messages[-10:]
            
        except KeyboardInterrupt:
            print("\nExiting chat...")
            break

if __name__ == "__main__":
    chat_loop()
