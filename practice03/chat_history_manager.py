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

# 确保日志目录和文件存在
def ensure_log_directory():
    log_dir = "D:\\chat-log"
    log_file = os.path.join(log_dir, "log.txt")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"创建日志目录: {log_dir}")
    
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# 聊天历史关键信息日志\n")
            f.write(f"创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        print(f"创建日志文件: {log_file}")
    
    return log_file

# 提取关键信息（5W规则）
def extract_key_info(chat_history, env):
    print("\n=== 开始提取关键信息 ===")
    
    # 构建提取提示词
    extract_prompt = {
        "role": "system",
        "content": "请从以下聊天记录中提取关键信息，按照5W规则（Who、What、When、Where、Why）进行提取。每个关键信息应该包含：\n1. Who：涉及的人物或实体\n2. What：发生的事件或行动\n3. When：时间（如果有）\n4. Where：地点（如果有）\n5. Why：原因或目的（如果有）\n\n请以JSON格式返回多条关键信息，每条信息包含上述5个字段。"
    }
    
    # 调用LLM进行提取
    extract_messages = [extract_prompt] + chat_history
    extraction, tokens, elapsed = call_llm(extract_messages, env)
    
    if extraction:
        print(f"提取完成，使用token: {tokens}，耗时: {elapsed:.2f}秒")
        
        # 解析提取结果
        try:
            # 尝试从JSON格式解析
            if extraction.strip().startswith('{') or extraction.strip().startswith('['):
                key_infos = json.loads(extraction)
            else:
                # 如果不是纯JSON，尝试提取JSON部分
                import re
                json_match = re.search(r'\{[^}]*\}|\[[^\]]*\]', extraction)
                if json_match:
                    key_infos = json.loads(json_match.group(0))
                else:
                    print("无法解析提取结果，使用原始文本")
                    key_infos = [{"Who": "未知", "What": extraction, "When": "", "Where": "", "Why": ""}]
            
            # 确保是列表格式
            if not isinstance(key_infos, list):
                key_infos = [key_infos]
            
            return key_infos
        except Exception as e:
            print(f"解析提取结果失败: {str(e)}")
            return [{"Who": "未知", "What": extraction, "When": "", "Where": "", "Why": ""}]
    else:
        print("提取失败")
        return []

# 记录关键信息到日志文件
def log_key_info(key_infos):
    log_file = ensure_log_directory()
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        for i, info in enumerate(key_infos, 1):
            f.write(f"关键信息 {i}:\n")
            f.write(f"  Who: {info.get('Who', '未知')}\n")
            f.write(f"  What: {info.get('What', '未知')}\n")
            f.write(f"  When: {info.get('When', '未知')}\n")
            f.write(f"  Where: {info.get('Where', '未知')}\n")
            f.write(f"  Why: {info.get('Why', '未知')}\n")
        f.write("\n")
    
    print(f"关键信息已记录到: {log_file}")

# 读取聊天历史日志
def read_chat_log():
    log_file = ensure_log_directory()
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

# 查找聊天历史
def search_chat_history(user_query, env):
    print("\n=== 查找聊天历史 ===")
    
    # 读取日志内容
    log_content = read_chat_log()
    
    # 构建查找提示词
    search_prompt = {
        "role": "system",
        "content": f"以下是聊天历史日志内容：\n{log_content}\n\n请根据用户的查询，从上述日志中查找相关信息并提供回答。如果没有相关信息，请说明。"
    }
    
    # 调用LLM进行查找
    search_messages = [search_prompt, {"role": "user", "content": user_query}]
    response, tokens, elapsed = call_llm(search_messages, env)
    
    if response:
        print(f"查找完成，使用token: {tokens}，耗时: {elapsed:.2f}秒")
        return response
    else:
        print("查找失败")
        return "无法查找聊天历史，请稍后再试。"

# 检查是否需要查找聊天历史
def should_search_chat_history(user_input):
    # 检查是否以/search开头
    if user_input.strip().startswith('/search'):
        return True
    
    # 检查是否包含查找聊天历史的关键词
    search_keywords = ['查找聊天历史', '查看聊天记录', '历史记录', '之前的对话', '之前说过']
    for keyword in search_keywords:
        if keyword in user_input:
            return True
    
    return False

# 主聊天函数
def chat_with_history_management():
    env = load_env()
    if not env:
        return
    
    print("=== 聊天历史管理功能演示 ===")
    print("Type your message and press Enter")
    print("Press Ctrl+C to exit")
    print("\n功能说明：")
    print("1. 每5次聊天自动提取关键信息并记录到 D:\chat-log\log.txt")
    print("2. 输入以'/search'开头的消息可查找聊天历史")
    print("3. 表达'查找聊天历史'等意思也会触发历史查询")
    print()
    
    chat_history = []
    chat_count = 0
    
    try:
        while True:
            # 检查是否需要提取关键信息
            if chat_count > 0 and chat_count % 5 == 0:
                print("\n⚠️  检测到已进行5次聊天，开始提取关键信息...")
                key_infos = extract_key_info(chat_history, env)
                if key_infos:
                    log_key_info(key_infos)
                    print("✅  关键信息提取和记录完成")
                print()
            
            # 获取用户输入
            user_input = input("You: ")
            if not user_input:
                continue
            
            # 检查是否需要查找聊天历史
            if should_search_chat_history(user_input):
                # 执行聊天历史查找
                search_result = search_chat_history(user_input, env)
                print(f"Assistant: {search_result}")
                
                # 显示性能信息
                print(f"\n=== Performance ===")
                # 注意：这里没有单独的性能统计，因为已经在search_chat_history函数中显示了
                print()
                continue
            
            # 添加用户消息到聊天历史
            chat_history.append({"role": "user", "content": user_input})
            chat_count += 1
            
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
    chat_with_history_management()
