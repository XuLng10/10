import os
import sys
import time
import json
import http.client
import select
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, List


MAX_TURNS = 5
MAX_CONTEXT_LENGTH = 3000
LOG_FILE_PATH = r"E:\tsgc\trae wenjian\chat-log.txt"
EXTRACT_INTERVAL = 5


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
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
    parsed = urlparse(base_url)
    return parsed.scheme, parsed.netloc, parsed.path.rstrip('/') or ''


def call_llm_api(base_url: str, model: str, api_key: str,
                 messages: list, timeout: int = 60) -> Dict[str, Any]:
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


def stream_chat_completions(base_url: str, model: str, api_key: str,
                            messages: list, timeout: int = 60) -> str:
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
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)

    try:
        conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()

        if response.status != 200:
            raise Exception(f"API请求失败: {response.status}")

        full_content = []
        for line in response:
            line = line.decode('utf-8').strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    json_data = json.loads(data)
                    delta = json_data.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        print(content, end='', flush=True)
                        full_content.append(content)
                except json.JSONDecodeError:
                    continue

        return ''.join(full_content)

    finally:
        conn.close()


def ensure_log_directory():
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)


def append_to_log(content: str):
    ensure_log_directory()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(f"\n[{timestamp}]\n{content}\n")


def extract_key_info(messages: list, base_url: str, model: str, api_key: str, timeout: int) -> str:
    history_text = "\n".join([
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages
    ])

    extract_prompt = f"""请从以下聊天记录中提取关键信息，按照5W规则提取：
- Who（谁）：执行动作的主体
- What（做了什么）：具体的行为或事件
- When（什么时候）：时间信息（如果存在）
- Where（在何处）：地点信息（如果存在）
- Why（为什么）：原因或目的（如果存在）

请以JSON格式输出，每条记录包含以上字段（不存在的字段可以为空字符串）。

聊天记录：
{history_text}

请提取关键信息并输出JSON数组格式："""

    extract_messages = [
        {"role": "system", "content": "你是一个关键信息提取助手。请从聊天记录中提取关键信息，用JSON格式输出。"},
        {"role": "user", "content": extract_prompt}
    ]

    response = call_llm_api(base_url, model, api_key, extract_messages, timeout)
    extracted = response['choices'][0]['message']['content']

    try:
        json_start = extracted.find('[')
        json_end = extracted.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            json_str = extracted[json_start:json_end]
            records = json.loads(json_str)
            for record in records:
                log_entry = f"Who: {record.get('Who', '')} | What: {record.get('What', '')} | When: {record.get('When', '')} | Where: {record.get('Where', '')} | Why: {record.get('Why', '')}"
                append_to_log(log_entry)
            return f"成功提取{len(records)}条关键信息到日志"
    except Exception:
        append_to_log(extracted)
        return "关键信息已记录"

    return "关键信息提取完成"


def search_chat_history(query: str) -> str:
    if not os.path.exists(LOG_FILE_PATH):
        return "聊天历史记录文件不存在"

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            history = f.read()

        if not history.strip():
            return "聊天历史记录为空"

        return f"【聊天历史记录】\n{history}\n\n【用户查询】{query}"
    except Exception as e:
        return f"读取聊天历史失败: {str(e)}"


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def count_turns(messages: list) -> int:
    turns = 0
    for msg in messages:
        if msg["role"] == "user":
            turns += 1
    return turns


def should_summarize(messages: list) -> Tuple[bool, str]:
    turns = count_turns(messages)
    if turns > MAX_TURNS:
        return True, f"聊天轮数({turns})超过上限({MAX_TURNS})"

    total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)
    if total_tokens > MAX_CONTEXT_LENGTH:
        return True, f"上下文长度({total_tokens} tokens)超过上限({MAX_CONTEXT_LENGTH} tokens)"

    return False, ""


def should_extract_key_info(turns_since_last_extract: int) -> bool:
    return turns_since_last_extract >= EXTRACT_INTERVAL


def summarize_messages(messages: list, base_url: str, model: str, api_key: str, timeout: int) -> list:
    print("\n" + "=" * 60)
    print("聊天记录压缩中...")
    print("=" * 60)

    total_turns = count_turns(messages)
    preserve_count = int(total_turns * 0.3)
    summarize_count = total_turns - preserve_count

    if summarize_count < 1:
        summarize_count = 1
        preserve_count = total_turns - summarize_count

    messages_to_summarize = []
    user_count = 0
    for m in messages:
        if m["role"] == "user":
            user_count += 1
        if user_count <= summarize_count:
            messages_to_summarize.append(m)

    messages_to_preserve = messages[len(messages_to_summarize):]

    history_text = "\n".join([
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages_to_summarize
    ])

    summarize_prompt = f"""请将以下聊天记录压缩成简洁的摘要，保留关键信息和要点。摘要应该能够代替原始对话内容继续进行有意义的对话。

需要压缩的聊天记录：
{history_text}

请生成一段压缩后的摘要："""

    summarize_messages = [
        {"role": "system", "content": "你是一个聊天记录压缩助手。请将聊天记录压缩成简洁的摘要。"},
        {"role": "user", "content": summarize_prompt}
    ]

    response = call_llm_api(base_url, model, api_key, summarize_messages, timeout)
    summary = response['choices'][0]['message']['content']

    print(f"\n压缩摘要：\n{summary[:200]}...")

    new_messages = [
        {"role": "system", "content": f"【之前的聊天记录摘要】：\n{summary}\n【以上是之前对话的压缩摘要】"}
    ]
    new_messages.extend(messages_to_preserve)

    print(f"\n压缩完成：{summarize_count}轮对话被压缩为摘要，保留{preserve_count}轮对话")
    print("=" * 60)

    return new_messages


def get_user_input(prompt: str = "你: ") -> str:
    try:
        sys.stdout.write(prompt)
        sys.stdout.flush()

        input_chars = []
        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == '\n':
                    break
                elif char == '\x7f':
                    if input_chars:
                        input_chars.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ord(char) == 27:
                    sys.stdin.read(2)
                else:
                    input_chars.append(char)
                    sys.stdout.write(char)
                    sys.stdout.flush()

        return ''.join(input_chars)
    except OSError:
        return input()


def print_banner():
    print("=" * 60)
    print("AI智能体终端聊天 - 带上下文压缩与历史记录")
    print("=" * 60)
    print(f"压缩策略：")
    print(f"  - 聊天轮数超过 {MAX_TURNS} 轮时触发压缩")
    print(f"  - 上下文长度超过 {MAX_CONTEXT_LENGTH} tokens 时触发压缩")
    print(f"  - 前70%对话压缩为摘要，保留最后30%对话")
    print(f"\n历史记录：")
    print(f"  - 每 {EXTRACT_INTERVAL} 轮对话提取一次关键信息(5W规则)")
    print(f"  - 记录到: {LOG_FILE_PATH}")
    print("=" * 60)
    print("提示: 输入消息后按回车发送，按 Ctrl+C 退出")
    print("=" * 60)


def main():
    print_banner()

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

        messages = []
        turns_since_last_extract = 0

        while True:
            try:
                user_input = get_user_input("你: ")
                if not user_input.strip():
                    continue

                should_search = (
                    user_input.strip().startswith("/search") or
                    "查找聊天历史" in user_input or
                    "搜索聊天记录" in user_input or
                    "查看历史记录" in user_input
                )

                if should_search:
                    print("\n[正在搜索聊天历史...]\n")
                    history_content = search_chat_history(user_input)
                    search_messages = [
                        {"role": "system", "content": "你是一个聊天历史查询助手。请根据提供的聊天历史记录回答用户的问题。"},
                        {"role": "user", "content": history_content}
                    ]
                    response = call_llm_api(base_url, model, api_key, search_messages, timeout)
                    result = response['choices'][0]['message']['content']
                    print(f"AI: {result}\n")
                    continue

                should_compact, reason = should_summarize(messages)
                if should_compact:
                    messages = summarize_messages(messages, base_url, model, api_key, timeout)

                messages.append({"role": "user", "content": user_input})

                print("\nAI: ", end='', flush=True)

                start_time = time.time()

                assistant_content = stream_chat_completions(
                    base_url, model, api_key, messages, timeout
                )

                end_time = time.time()
                elapsed_time = end_time - start_time

                messages.append({"role": "assistant", "content": assistant_content})

                turns_since_last_extract += 1

                if should_extract_key_info(turns_since_last_extract):
                    print("\n\n[正在提取关键信息...]")
                    extract_result = extract_key_info(messages, base_url, model, api_key, timeout)
                    print(f"[{extract_result}]")
                    turns_since_last_extract = 0

                turns = count_turns(messages)
                total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)

                print(f"\n\n[耗时: {round(elapsed_time, 2)}秒] [聊天轮数: {turns}] [估计tokens: {total_tokens}]")
                print("-" * 60)

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
