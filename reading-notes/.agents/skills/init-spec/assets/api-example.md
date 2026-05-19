# LLM API 客户端工具 - API 设计文档

## 一、模块结构

```
practice01/
└── llm_client.py
    ├── load_env()          # 加载配置
    ├── call_llm()          # 调用 LLM API
    ├── calculate_stats()   # 计算统计指标
    ├── print_results()     # 输出结果
    └── main()              # 主入口
```

---

## 二、全局变量

| 变量名 | 类型 | 说明 |
| --- | --- | --- |
| `ENV_PATH` | str | .env 文件路径，固定为 `../.env` |
| `DEFAULT_TIMEOUT` | int | 默认超时时间，30 秒 |
| `API_ENDPOINT` | str | API 端点，固定为 `/chat/completions` |

---

## 三、方法详细设计

### 3.1 `load_env(env_path: str) -> dict`

**功能**：从指定路径读取并解析 .env 配置文件

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `env_path` | str | .env 文件的绝对路径或相对路径 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `dict` | 包含配置参数的字典，键为参数名，值为参数值 |

**异常处理**：
- 文件不存在：抛出 `FileNotFoundError`
- 参数缺失：抛出 `ValueError`

**伪代码**：
```plaintext
FUNCTION load_env(env_path):
    IF 文件不存在 env_path:
        抛出 FileNotFoundError("配置文件不存在")
    
    创建空字典 config
    
    打开 env_path 文件逐行读取:
        FOR 每一行 line:
            去除首尾空白
            IF line 以 '#' 开头 OR 不包含 '=':
                跳过
            
            分割 line 为 key 和 value (以 '=' 为分隔符)
            config[key] = value
    
    检查必需参数是否存在:
        required_params = ['LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_KEY']
        FOR param IN required_params:
            IF param NOT IN config:
                抛出 ValueError(f"缺少必需参数: {param}")
    
    RETURN config
```

---

### 3.2 `call_llm(config: dict, prompt: str) -> tuple`

**功能**：使用 HTTP POST 请求调用 LLM API

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `config` | dict | 包含 LLM_BASE_URL、LLM_MODEL、LLM_API_KEY 的配置字典 |
| `prompt` | str | 用户输入的提示词 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `tuple` | 三元组 `(response_data, elapsed_time)` |
| `response_data` | dict | API 响应的 JSON 数据 |
| `elapsed_time` | float | 请求耗时（秒） |

**伪代码**：
```plaintext
FUNCTION call_llm(config, prompt):
    # 构建请求 URL
    base_url = config['LLM_BASE_URL']
    full_url = base_url + '/chat/completions'
    
    # 解析 URL
    从 full_url 提取 protocol, host, path
    
    # 构建请求体
    request_body = {
        "model": config['LLM_MODEL'],
        "messages": [{"role": "user", "content": prompt}]
    }
    
    # 记录开始时间
    start_time = 当前时间戳
    
    # 发起 HTTP POST 请求
    IF protocol == 'https':
        创建 HTTPSConnection
    ELSE:
        创建 HTTPConnection
    
    设置请求头:
        Content-Type: application/json
        Authorization: Bearer {config['LLM_API_KEY']}
    
    发送 POST 请求到 path，数据为 JSON 序列化的 request_body
    
    获取响应状态码和响应体
    
    IF 状态码 != 200:
        抛出 HTTPError(f"API 请求失败: {状态码}")
    
    # 解析响应 JSON
    response_data = JSON 解析响应体
    
    # 计算耗时
    elapsed_time = 当前时间戳 - start_time
    
    RETURN (response_data, elapsed_time)
```

---

### 3.3 `calculate_stats(response_data: dict, elapsed_time: float) -> dict`

**功能**：从 API 响应中提取并计算统计指标

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `response_data` | dict | API 响应的 JSON 数据 |
| `elapsed_time` | float | 请求耗时（秒） |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `dict` | 包含统计指标的字典 |

**返回值字段**：
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `model` | str | 模型名称 |
| `prompt_tokens` | int | 提示词 token 数 |
| `completion_tokens` | int | 生成内容 token 数 |
| `total_tokens` | int | 总 token 数 |
| `elapsed_time` | float | 响应时间（秒） |
| `tokens_per_second` | float | 处理速度（token/s） |

**伪代码**：
```plaintext
FUNCTION calculate_stats(response_data, elapsed_time):
    # 提取模型名称
    model = response_data['model']
    
    # 提取 token 使用情况
    usage = response_data['usage']
    prompt_tokens = usage['prompt_tokens']
    completion_tokens = usage['completion_tokens']
    total_tokens = usage['total_tokens']
    
    # 计算处理速度
    IF elapsed_time > 0:
        tokens_per_second = total_tokens / elapsed_time
    ELSE:
        tokens_per_second = 0.0
    
    # 构建统计结果
    stats = {
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': total_tokens,
        'elapsed_time': elapsed_time,
        'tokens_per_second': tokens_per_second
    }
    
    RETURN stats
```

---

### 3.4 `print_results(stats: dict, response_text: str)`

**功能**：格式化输出统计结果和响应内容

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `stats` | dict | 包含统计指标的字典 |
| `response_text` | str | LLM 返回的响应文本 |

**返回值**：无

**输出格式**：
```
========================================
LLM API 调用统计
========================================
模型: gpt-3.5-turbo
提示词 Token: 15
生成 Token: 42
总 Token: 57
响应时间: 2.30s
处理速度: 24.78 token/s
========================================
响应内容:
你好！我是一个 AI 助手。
```

**伪代码**：
```plaintext
FUNCTION print_results(stats, response_text):
    打印 "========================================"
    打印 "LLM API 调用统计"
    打印 "========================================"
    打印 f"模型: {stats['model']}"
    打印 f"提示词 Token: {stats['prompt_tokens']}"
    打印 f"生成 Token: {stats['completion_tokens']}"
    打印 f"总 Token: {stats['total_tokens']}"
    打印 f"响应时间: {stats['elapsed_time']:.2f}s"
    打印 f"处理速度: {stats['tokens_per_second']:.2f} token/s"
    打印 "========================================"
    打印 "响应内容:"
    打印 response_text
```

---

### 3.5 `main()`

**功能**：主程序入口，协调整个流程

**执行流程**：
1. 加载配置
2. 获取用户输入提示词
3. 调用 LLM API
4. 计算统计指标
5. 提取响应文本
6. 输出结果

**伪代码**：
```plaintext
FUNCTION main():
    TRY:
        # 1. 加载配置
        config = load_env('../.env')
        
        # 2. 获取用户输入
        prompt = input("请输入您的问题: ")
        
        # 3. 调用 LLM API
        response_data, elapsed_time = call_llm(config, prompt)
        
        # 4. 计算统计指标
        stats = calculate_stats(response_data, elapsed_time)
        
        # 5. 提取响应文本
        response_text = response_data['choices'][0]['message']['content']
        
        # 6. 输出结果
        print_results(stats, response_text)
    
    EXCEPT FileNotFoundError AS e:
        打印 f"错误: {e}. 请先复制 env.example 为 .env 并填写配置"
    
    EXCEPT ValueError AS e:
        打印 f"配置错误: {e}"
    
    EXCEPT Exception AS e:
        打印 f"发生错误: {e}"
```

---

## 四、数据流转图

```
用户输入
    ↓
load_env() → config 字典
    ↓
call_llm(config, prompt) → response_data, elapsed_time
    ↓
calculate_stats(response_data, elapsed_time) → stats 字典
    ↓
提取 response_text
    ↓
print_results(stats, response_text) → 控制台输出
```