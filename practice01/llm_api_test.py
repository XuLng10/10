import os
import time
import json
import http.client
from urllib.parse import urlparse
from typing import Dict, Any, Tuple


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


def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("LLM API调用测试 - Token消耗统计")
    print("=" * 60)


def main():
    """主函数"""
    print_banner()

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

        messages = [
            {"role": "user", "content": "请用一句话介绍Python编程语言的特点。"}
        ]

        print(f"\n发送请求:")
        print(f"  Messages: {json.dumps(messages, ensure_ascii=False)}")

        print("\n" + "-" * 60)
        print("响应内容:")
        start_time = time.time()

        response = call_llm_api(base_url, model, api_key, messages, timeout)

        end_time = time.time()
        elapsed_time = end_time - start_time

        content = response['choices'][0]['message']['content']
        print(f"  {content}")

        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)

        tokens_per_second = (completion_tokens / elapsed_time) if elapsed_time > 0 else 0

        print("\n" + "-" * 60)
        print("统计信息:")
        print(f"  总耗时: {elapsed_time:.3f}秒")
        print(f"  输入Token数: {prompt_tokens}")
        print(f"  输出Token数: {completion_tokens}")
        print(f"  总Token数: {total_tokens}")
        print(f"  处理速度: {tokens_per_second:.2f} tokens/s")

        print("\n" + "=" * 60)
        print("调用成功！")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("请按照以下步骤操作:")
        print("1. 复制 env.example 文件为 .env")
        print("2. 在 .env 文件中填入正确的LLM配置信息")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
