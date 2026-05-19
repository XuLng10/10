import os
import sys
import time
import json
import http.client
import select
import subprocess
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, List, Optional, Union
import re


MAX_TURNS = 5
MAX_CONTEXT_LENGTH = 3000
LOG_FILE_PATH = r"E:\tsgc\trae wenjian\chat-log.txt"
EXTRACT_INTERVAL = 5
SKILLS_DIR = r"E:\tsgc\trae wenjian\.agents\skills"


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
        raise FileNotFoundError(f"环境文件 {env_path} 不存在，请从 env.example 复制并配置")
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
            raise Exception(f"API 请求失败：{response.status} - {response_data}")

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
            raise Exception(f"API 请求失败：{response.status}")

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


def anythingllm_query(message: str, api_key: str, workspace_slug: str = "default") -> str:
    url = f"http://localhost:3001/api/v1/workspace/{workspace_slug}/chat"

    payload = {
        "message": message,
        "mode": "query"
    }

    payload_json = json.dumps(payload, ensure_ascii=False)

    curl_command = [
        "curl",
        "-X", "POST",
        url,
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json; charset=utf-8",
        "-d", payload_json,
        "--compressed"
    ]

    try:
        result = subprocess.Popen(
            curl_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = result.communicate()

        if result.returncode != 0:
            error_msg = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
            return f"错误：{error_msg}"

        try:
            stdout_str = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
            response = json.loads(stdout_str)
            if 'text' in response:
                return response['text']
            elif 'message' in response:
                return response['message']
            else:
                return json.dumps(response, ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            stdout_str = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
            return f"响应解析失败：{stdout_str}"

    except Exception as e:
        return f"调用失败：{str(e)}"


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

    extract_prompt = f"""请从以下聊天记录中提取关键信息，按照 5W 规则提取：
- Who（谁）：执行动作的主体
- What（做了什么）：具体的行为或事件
- When（什么时候）：时间信息（如果存在）
- Where（在何处）：地点信息（如果存在）
- Why（为什么）：原因或目的（如果存在）

请以 JSON 格式输出，每条记录包含以上字段（不存在的字段可以为空字符串）。

聊天记录：
{history_text}

请提取关键信息并输出 JSON 数组格式："""

    extract_messages = [
        {"role": "system", "content": "你是一个关键信息提取助手。请从聊天记录中提取关键信息，用 JSON 格式输出。"},
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
        return f"读取聊天历史失败：{str(e)}"


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
        return True, f"聊天轮数 ({turns}) 超过上限 ({MAX_TURNS})"

    total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)
    if total_tokens > MAX_CONTEXT_LENGTH:
        return True, f"上下文长度 ({total_tokens} tokens) 超过上限 ({MAX_CONTEXT_LENGTH} tokens)"

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


def list_available_skills() -> List[Dict[str, str]]:
    skills = []

    if not os.path.exists(SKILLS_DIR):
        return skills

    for item in os.listdir(SKILLS_DIR):
        item_path = os.path.join(SKILLS_DIR, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if content.startswith('---'):
                        end_marker = content.find('---', 3)
                        if end_marker != -1:
                            front_matter = content[3:end_marker].strip()
                            name = None
                            description = None
                            for line in front_matter.split('\n'):
                                line = line.strip()
                                if line.startswith('name:'):
                                    name = line.split(':', 1)[1].strip()
                                elif line.startswith('description:'):
                                    description = line.split(':', 1)[1].strip()

                            if name and description:
                                skills.append({
                                    "name": name,
                                    "description": description
                                })
                except Exception:
                    continue

    return skills


def load_skill_content(skill_name: str) -> str:
    skill_file = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")

    if not os.path.exists(skill_file):
        return f"技能 '{skill_name}' 不存在"

    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.startswith('---'):
            end_marker = content.find('---', 3)
            if end_marker != -1:
                body = content[end_marker + 3:].strip()
                return body

        return content.strip()
    except Exception as e:
        return f"读取技能内容失败：{str(e)}"


def get_skills_system_prompt() -> str:
    skills = list_available_skills()
    skills_json = json.dumps({"skills": skills}, ensure_ascii=False)

    prompt = f"""你是一个具备技能调用能力的AI助手。

可用技能列表：
{skills_json}

技能调用规则：
1. 分析用户请求，判断是否需要使用技能
2. 如果需要使用技能，输出技能调用指令
3. 如果不需要使用技能，可以直接回答用户

技能调用格式：
用 [function name=load_skill_content][parameter name=skill_name]技能名称[/parameter][/function] 格式调用技能"""

    return prompt


def parse_skill_call(content: str) -> Tuple[bool, str]:
    param_pattern = r'\[parameter name=skill_name\](.+?)\[/parameter\]'
    param_match = re.search(param_pattern, content)
    if param_match:
        skill_name = param_match.group(1).strip()
        if skill_name and skill_name not in ['', '[/parameter]']:
            return True, skill_name

    func_name_pattern = r'\[function name=(\w+)\]'
    func_match = re.search(func_name_pattern, content)
    if func_match:
        skill_name = func_match.group(1).strip()
        if skill_name and skill_name != 'load_skill_content':
            return True, skill_name

    standard_pattern = r'\[function name=load_skill_content\]\[parameter name=skill_name\](.+?)\[/parameter\]\[/function\]'
    std_match = re.search(standard_pattern, content)
    if std_match:
        skill_name = std_match.group(1).strip()
        if skill_name:
            return True, skill_name

    return False, ""


def get_user_input(prompt: str = "你：") -> str:
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
    print("AI 智能体终端聊天 - 带链式工具调用")
    print("=" * 60)
    print(f"压缩策略：")
    print(f"  - 聊天轮数超过 {MAX_TURNS} 轮时触发压缩")
    print(f"  - 上下文长度超过 {MAX_CONTEXT_LENGTH} tokens 时触发压缩")
    print(f"  - 前 70% 对话压缩为摘要，保留最后 30% 对话")
    print(f"\n历史记录：")
    print(f"  - 每 {EXTRACT_INTERVAL} 轮对话提取一次关键信息 (5W 规则)")
    print(f"  - 记录到：{LOG_FILE_PATH}")
    print(f"\nAnythingLLM 集成：")
    print(f"  - 提到'文档仓库'、'文件仓库'、'仓库'时自动查询")
    print(f"\n技能系统：")
    print(f"  - 自动读取 .agents/skills 目录下的技能")
    print(f"  - 支持链式工具调用（Chained Tool Calls）")
    print("=" * 60)
    print("提示：输入消息后按回车发送，按 Ctrl+C 退出")
    print("=" * 60)


# ==================== 链式工具调用相关功能 ====================

class ChainedCallContext:
    """链式调用上下文管理器"""

    def __init__(self, max_iterations: int = 10):
        self.steps: List[Dict[str, Any]] = []
        self.variables: Dict[str, Any] = {}
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.final_answer = None
        self.is_complete = False

    def add_step(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """记录一步工具调用"""
        step = {
            "iteration": self.current_iteration,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": time.time()
        }
        self.steps.append(step)
        self.current_iteration += 1

    def set_variable(self, name: str, value: Any):
        """设置中间变量"""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取中间变量"""
        return self.variables.get(name, default)

    def get_last_result(self) -> Optional[Any]:
        """获取上一步的结果"""
        if self.steps:
            return self.steps[-1]["result"]
        return None

    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数"""
        return self.current_iteration >= self.max_iterations

    def get_steps_summary(self) -> str:
        """获取步骤摘要"""
        summary = []
        for i, step in enumerate(self.steps, 1):
            summary.append(f"步骤 {i}: {step['tool_name']}(参数={json.dumps(step['arguments'], ensure_ascii=False)}) -> {str(step['result'])[:100]}...")
        return "\n".join(summary)


def build_analysis_prompt(user_request: str, context: ChainedCallContext) -> str:
    """构建链式调用分析提示词"""
    
    steps_history = ""
    if context.steps:
        steps_history = "\n已执行的步骤：\n" + context.get_steps_summary()
    
    variables_info = ""
    if context.variables:
        variables_info = "\n当前变量：\n" + json.dumps(context.variables, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个具备链式工具调用能力的AI助手。请根据用户请求和已执行的步骤，决定下一步操作。

【用户请求】
{user_request}

{steps_history}

{variables_info}

【决策规则】
1. 分析当前状态，判断任务是否已完成
2. 如果任务已完成，直接总结回答用户
3. 如果任务未完成，选择合适的工具继续执行
4. 可以使用上一步的结果作为当前步骤的输入参数

【可用工具】
- file_search(keyword, directory): 搜索目录下包含关键词的文件
- read_file(file_path): 读取文件内容
- write_file(file_path, content): 写入文件内容
- web_fetch(url): 获取网页内容
- load_skill_content(skill_name): 加载技能内容

【输出格式】
请严格按照以下 JSON 格式输出：

完成任务时：
{{"done": true, "answer": "最终回答内容"}}

继续调用工具时：
{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}

请确保输出是有效的 JSON 格式，不要包含其他内容。"""

    return prompt


def extract_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """从响应中提取 JSON 内容"""
    try:
        content = content.strip()
        
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        content = content.strip()
        
        return json.loads(content)
    except Exception:
        return None


def parse_llm_response(response: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """解析 LLM 响应，支持 JSON content 格式和 tool_calls 格式"""
    try:
        message = response.get('choices', [{}])[0].get('message', {})
        
        if 'tool_calls' in message and message['tool_calls']:
            tool_call = message['tool_calls'][0]
            tool_name = tool_call.get('function', {}).get('name')
            arguments = json.loads(tool_call.get('function', {}).get('arguments', '{}'))
            return False, tool_name, arguments
        
        content = message.get('content', '')
        if content:
            json_data = extract_json_from_response(content)
            if json_data:
                if json_data.get('done', False):
                    return True, None, json_data.get('answer')
                elif 'tool_call' in json_data:
                    tool_call = json_data['tool_call']
                    return False, tool_call.get('name'), tool_call.get('arguments', {})
        
        return False, None, None
    except Exception as e:
        print(f"解析 LLM 响应失败: {e}")
        return False, None, None


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """执行工具调用"""
    try:
        if tool_name == 'file_search':
            keyword = arguments.get('keyword', '')
            directory = arguments.get('directory', '.')
            return file_search(keyword, directory)
        
        elif tool_name == 'read_file':
            file_path = arguments.get('file_path', '')
            return read_file(file_path)
        
        elif tool_name == 'write_file':
            file_path = arguments.get('file_path', '')
            content = arguments.get('content', '')
            return write_file(file_path, content)
        
        elif tool_name == 'web_fetch':
            url = arguments.get('url', '')
            return web_fetch(url)
        
        elif tool_name == 'load_skill_content':
            skill_name = arguments.get('skill_name', '')
            return load_skill_content(skill_name)
        
        else:
            return f"未知工具: {tool_name}"
    except Exception as e:
        return f"工具执行失败: {str(e)}"


def file_search(keyword: str, directory: str) -> str:
    """搜索目录下包含关键词的文件"""
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if keyword in content:
                            results.append(file_path)
                except Exception:
                    continue
        if results:
            return "\n".join(results)
        else:
            return f"未找到包含 '{keyword}' 的文件"
    except Exception as e:
        return f"搜索失败: {str(e)}"


def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """写入文件内容"""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"文件写入成功: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"


def web_fetch(url: str) -> str:
    """获取网页内容"""
    try:
        parsed = urlparse(url)
        protocol = parsed.scheme
        host = parsed.netloc
        path = parsed.path or '/'
        
        if protocol == 'https':
            conn = http.client.HTTPSConnection(host, timeout=30)
        else:
            conn = http.client.HTTPConnection(host, timeout=30)
        
        conn.request("GET", path)
        response = conn.getresponse()
        content = response.read().decode('utf-8', errors='ignore')
        conn.close()
        
        return content[:5000] if len(content) > 5000 else content
    except Exception as e:
        return f"获取网页失败: {str(e)}"


def execute_chained_tool_call(
    user_request: str,
    base_url: str,
    model: str,
    api_key: str,
    timeout: int = 60,
    max_iterations: int = 10
) -> str:
    """执行链式工具调用"""
    context = ChainedCallContext(max_iterations=max_iterations)
    
    print(f"\n=== 开始链式工具调用 ===")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    print("-" * 60)
    
    for iteration in range(max_iterations):
        print(f"\n【迭代 {iteration + 1}】")
        
        if context.is_max_iterations_reached():
            print("已达到最大迭代次数，终止调用")
            break
        
        analysis_prompt = build_analysis_prompt(user_request, context)
        
        messages = [
            {"role": "system", "content": get_skills_system_prompt()},
            {"role": "user", "content": analysis_prompt}
        ]
        
        try:
            response = call_llm_api(base_url, model, api_key, messages, timeout)
            is_done, tool_name, data = parse_llm_response(response)
            
            if is_done:
                print(f"任务完成: {str(data)[:200]}...")
                context.final_answer = str(data)
                context.is_complete = True
                break
            
            if tool_name and data:
                print(f"调用工具: {tool_name}")
                print(f"参数: {json.dumps(data, ensure_ascii=False)}")
                
                result = execute_tool(tool_name, data)
                print(f"工具执行结果: {str(result)[:200]}...")
                
                context.add_step(tool_name, data, result)
                context.set_variable(f"last_result_{tool_name}", result)
                
            else:
                print("LLM 未返回有效的工具调用指令")
                context.final_answer = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                break
                
        except Exception as e:
            print(f"迭代 {iteration + 1} 执行失败: {e}")
            break
    
    print("\n" + "=" * 60)
    print("=== 链式调用结束 ===")
    
    if context.final_answer:
        return context.final_answer
    elif context.steps:
        return f"已完成 {len(context.steps)} 步操作，但未获得最终回答。步骤记录:\n{context.get_steps_summary()}"
    else:
        return "链式调用未完成任何操作"


def main():
    print_banner()

    try:
        env_vars = load_env_file()

        base_url = env_vars.get('LLM_BASE_URL')
        model = env_vars.get('LLM_MODEL')
        api_key = env_vars.get('LLM_API_KEY')
        timeout = int(env_vars.get('LLM_TIMEOUT', '60'))

        anythingllm_api_key = env_vars.get('ANYTHINGLLM_API_KEY')
        anythingllm_workspace = env_vars.get('ANYTHINGLLM_WORKSPACE_SLUG', 'default')

        if not all([base_url, model, api_key]):
            raise ValueError("缺少必要的 LLM 环境变量配置")

        print(f"\n已连接到：{base_url}")
        print(f"使用模型：{model}")
        if anythingllm_api_key:
            print(f"AnythingLLM 工作区：{anythingllm_workspace}")

        skills = list_available_skills()
        print(f"\n已加载技能：")
        for skill in skills:
            print(f"  - {skill['name']}: {skill['description']}")
        print()

        messages = []
        turns_since_last_extract = 0

        while True:
            try:
                user_input = get_user_input("你：")
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

                should_query_anythingllm = (
                    "文档仓库" in user_input or
                    "文件仓库" in user_input or
                    "仓库" in user_input
                )

                if should_query_anythingllm and anythingllm_api_key:
                    print("\n[正在查询文档仓库...]\n")
                    result = anythingllm_query(user_input, anythingllm_api_key, anythingllm_workspace)
                    print(f"文档仓库：{result}\n")
                    continue

                should_use_chained = (
                    "查找" in user_input and "文件" in user_input or
                    "读取" in user_input and ("文件" in user_input or ".txt" in user_input) or
                    "写入" in user_input and "文件" in user_input or
                    "访问" in user_input and ("网页" in user_input or "https://" in user_input) or
                    "总结" in user_input and ("文件" in user_input or "页面" in user_input)
                )

                if should_use_chained:
                    print("\n[检测到需要链式工具调用...]")
                    result = execute_chained_tool_call(
                        user_input, base_url, model, api_key, timeout
                    )
                    print(f"\n最终结果:\n{result}\n")
                    continue

                should_compact, reason = should_summarize(messages)
                if should_compact:
                    messages = summarize_messages(messages, base_url, model, api_key, timeout)

                messages.append({"role": "user", "content": user_input})

                skills_system_prompt = get_skills_system_prompt()
                api_messages = [
                    {"role": "system", "content": skills_system_prompt}
                ]
                api_messages.extend(messages)

                print("\nAI: ", end='', flush=True)

                start_time = time.time()

                assistant_content = stream_chat_completions(
                    base_url, model, api_key, api_messages, timeout
                )

                end_time = time.time()
                elapsed_time = end_time - start_time

                has_skill_call, skill_name = parse_skill_call(assistant_content)

                if has_skill_call:
                    print(f"\n\n[正在加载技能：{skill_name}...]\n")
                    skill_content = load_skill_content(skill_name)

                    skill_system_prompt = f"""请根据以下技能内容执行用户的请求：

【技能内容】
{skill_content}

【用户原始请求】
{user_input}

请严格按照技能内容中的规则和格式执行，输出最终结果。"""

                    skill_messages = [
                        {"role": "system", "content": skill_system_prompt},
                        {"role": "user", "content": user_input}
                    ]

                    print("AI: ", end='', flush=True)
                    final_content = stream_chat_completions(
                        base_url, model, api_key, skill_messages, timeout
                    )
                    messages.append({"role": "assistant", "content": final_content})
                else:
                    messages.append({"role": "assistant", "content": assistant_content})

                turns_since_last_extract += 1

                if should_extract_key_info(turns_since_last_extract):
                    print("\n\n[正在提取关键信息...]")
                    extract_result = extract_key_info(messages, base_url, model, api_key, timeout)
                    print(f"[{extract_result}]")
                    turns_since_last_extract = 0

                turns = count_turns(messages)
                total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)

                print(f"\n\n[耗时：{round(elapsed_time, 2)}秒] [聊天轮数：{turns}] [估计 tokens: {total_tokens}]")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n错误：{e}")

    except FileNotFoundError as e:
        print(f"\n错误：{e}")
        print("请按照以下步骤操作:")
        print("1. 复制 env.example 文件为 .env")
        print("2. 在 .env 文件中填入正确的 LLM 配置信息")
    except Exception as e:
        print(f"\n错误：{e}")


if __name__ == "__main__":
    main()
