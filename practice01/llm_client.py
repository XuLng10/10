import os
import json
import time
import http.client
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

# 访问LLM并统计信息
def call_llm():
    env = load_env()
    if not env:
        return
    
    # 解析URL
    parsed_url = urlparse(env['BASE_URL'])
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    
    # 构建请求数据
    data = {
        "model": env['MODEL'],
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": float(env.get('TEMPERATURE', 0.7)),
        "max_tokens": int(env.get('MAX_TOKENS', 1000))
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
        response_data = response.read().decode('utf-8')
        conn.close()
        
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 解析响应
        response_json = json.loads(response_data)
        if 'error' in response_json:
            print(f"Error: {response_json['error']['message']}")
            return
        
        # 提取token使用情况
        usage = response_json.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # 计算速度
        if elapsed_time > 0:
            tokens_per_second = total_tokens / elapsed_time
        else:
            tokens_per_second = 0
        
        # 打印结果
        print("=== LLM Call Results ===")
        print(f"Model: {env['MODEL']}")
        print(f"Prompt: Hello, how are you?")
        print(f"Response: {response_json['choices'][0]['message']['content'].strip()}")
        print(f"\n=== Token Usage ===")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Completion tokens: {completion_tokens}")
        print(f"Total tokens: {total_tokens}")
        print(f"\n=== Performance ===")
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print(f"Tokens per second: {tokens_per_second:.2f}")
        
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")

if __name__ == "__main__":
    call_llm()
