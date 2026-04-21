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

# 计算消息长度（近似token数）
def calculate_message_length(messages):
    total_length = 0
    for msg in messages:
        if 'content' in msg:
            total_length += len(msg['content'])
    return total_length

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
            return None, 0, elapsed_time
        
        # 提取token使用情况
        usage = response_json.get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        
        # 提取回复内容
        if 'choices' in response_json and len(response_json['choices']) > 0:
            content = response_json['choices'][0]['message']['content']
            return content, total_tokens, elapsed_time
        else:
            return None, 0, elapsed_time
            
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return None, 0, 0

# 生成聊天记录总结
def summarize_chat_history(chat_history, env):
    print("\n=== 开始总结聊天记录 ===")
    
    # 计算需要压缩的部分和保留的部分
    total_messages = len(chat_history)
    compress_count = int(total_messages * 0.7)
    keep_count = total_messages - compress_count
    
    # 分离需要压缩的部分和保留的部分
    compress_messages = chat_history[:compress_count]
    keep_messages = chat_history[compress_count:]
    
    # 构建总结提示词
    summary_prompt = {
        "role": "system",
        "content": "请对以下聊天记录进行简要总结，保留关键信息和对话主题，忽略不重要的细节。总结应该简洁明了，能够让新加入对话的人快速了解之前的讨论内容。"
    }
    
    # 调用LLM进行总结
    summary_messages = [summary_prompt] + compress_messages
    summary, tokens, elapsed = call_llm(summary_messages, env)
    
    if summary:
        print(f"总结完成，使用token: {tokens}，耗时: {elapsed:.2f}秒")
        
        # 构建新的聊天历史：总结 + 保留的原文
        new_chat_history = [
            {
                "role": "assistant",
                "content": f"【聊天历史总结】\n{summary}\n\n--- 以下是最近的对话内容 ---"
            }
        ] + keep_messages
        
        return new_chat_history
    else:
        print("总结失败，保留原始聊天记录")
        return chat_history

# 主聊天函数
def chat_with_summary():
    env = load_env()
    if not env:
        return
    
    print("=== 聊天记录总结功能演示 ===")
    print("Type your message and press Enter")
    print("Press Ctrl+C to exit")
    print("\n当聊天历史超过5轮或上下文长度超过3k时，会自动触发总结")
    print()
    
    chat_history = []
    
    try:
        while True:
            # 检查是否需要总结
            if len(chat_history) > 5 or calculate_message_length(chat_history) > 3000:
                print("\n⚠️  检测到聊天历史过长，开始总结...")
                chat_history = summarize_chat_history(chat_history, env)
                print("✅  总结完成，聊天历史已压缩")
                print()
            
            # 获取用户输入
            user_input = input("You: ")
            if not user_input:
                continue
            
            # 添加用户消息到聊天历史
            chat_history.append({"role": "user", "content": user_input})
            
            # 调用LLM获取回复
            print("Assistant: ", end="", flush=True)
            response, tokens, elapsed = call_llm(chat_history, env)
            
            if response:
                print(response)
                # 添加助手回复到聊天历史
                chat_history.append({"role": "assistant", "content": response})
                
                # 显示性能信息
                print(f"\n=== Performance ===")
                print(f"Time taken: {elapsed:.2f} seconds")
                print(f"Tokens used: {tokens}")
                if elapsed > 0:
                    print(f"Tokens per second: {tokens/elapsed:.2f}")
                print()
            else:
                print("No response from LLM")
                
    except KeyboardInterrupt:
        print("\nExiting chat...")

if __name__ == "__main__":
    chat_with_summary()
