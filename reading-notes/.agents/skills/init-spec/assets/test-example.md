# LLM API 客户端工具 - 测试文档

## 一、测试概述

### 1.1 测试目标
验证 LLM API 客户端工具的各项功能是否符合需求：
- 配置文件读取功能
- API 调用功能
- 统计指标计算功能
- 结果输出功能

### 1.2 测试范围
| 模块 | 测试类型 |
| --- | --- |
| `load_env()` | 单元测试 |
| `call_llm()` | 集成测试 |
| `calculate_stats()` | 单元测试 |
| `print_results()` | 单元测试 |
| `main()` | 集成测试 |

### 1.3 测试环境
- Python 3.8+
- 测试用配置文件：`test_env/.env`
- Mock LLM 服务（用于集成测试）

---

## 二、单元测试用例

### 2.1 `load_env()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-001 | 正常读取配置文件 | 完整的 .env 文件 | 返回包含所有参数的字典 |
| TC-002 | 配置文件不存在 | 不存在的文件路径 | 抛出 FileNotFoundError |
| TC-003 | 缺少必需参数 | 缺少 LLM_API_KEY 的 .env | 抛出 ValueError |
| TC-004 | 配置文件包含注释 | 包含 # 注释的 .env | 正确解析有效配置项 |
| TC-005 | 空配置文件 | 空的 .env 文件 | 抛出 ValueError（缺少参数） |

**测试数据示例**：
```env
# 完整配置示例
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=sk-xxxxxxxxxx
```

---

### 2.2 `calculate_stats()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-006 | 正常计算统计指标 | response_data 包含完整 usage，elapsed_time=2.0 | tokens_per_second = total_tokens / 2.0 |
| TC-007 | 零耗时情况 | elapsed_time=0 | tokens_per_second=0 |
| TC-008 | 大 token 数计算 | total_tokens=1000, elapsed_time=10 | tokens_per_second=100 |
| TC-009 | 小数耗时计算 | elapsed_time=2.35 | 正确计算速度（保留2位小数） |

**测试数据示例**：
```python
response_data = {
    "model": "gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 15,
        "completion_tokens": 42,
        "total_tokens": 57
    },
    "choices": [...]
}
elapsed_time = 2.35
```

---

### 2.3 `print_results()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-010 | 正常输出 | 完整的 stats 和 response_text | 按格式输出所有统计信息 |
| TC-011 | 空响应内容 | response_text="" | 输出"响应内容:"后为空 |
| TC-012 | 特殊字符响应 | response_text 包含换行符 | 正确显示换行 |

---

## 三、集成测试用例

### 3.1 `call_llm()` 集成测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-013 | 正常 API 调用 | 有效的配置和提示词 | 返回响应数据和耗时 |
| TC-014 | API 认证失败 | 无效的 API_KEY | 抛出 HTTPError（401） |
| TC-015 | 请求超时 | 超时时间内无响应 | 抛出超时异常 |
| TC-016 | 模型不存在 | 无效的模型名称 | 抛出 HTTPError（404） |
| TC-017 | HTTPS 请求 | HTTPS 协议的 API 地址 | 成功建立安全连接 |

---

### 3.2 端到端测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-018 | 完整流程测试 | 用户输入"Hello" | 输出完整统计信息和响应 |
| TC-019 | 中文提示词测试 | 用户输入中文问题 | 正确处理中文编码 |
| TC-020 | 长提示词测试 | 超过 100 token 的提示词 | 正确统计 token 消耗 |

---

## 四、测试步骤

### 4.1 单元测试步骤

```plaintext
1. 创建测试配置文件目录 test_env/
2. 在 test_env/ 中创建测试用 .env 文件
3. 编写单元测试脚本 test_llm_client.py
4. 运行测试：python -m pytest test_llm_client.py -v
```

### 4.2 集成测试步骤

```plaintext
1. 启动 Mock LLM 服务（或使用真实测试环境）
2. 配置测试用 .env 文件指向测试服务
3. 运行集成测试：python -m pytest test_integration.py -v
4. 验证响应状态码和响应内容格式
```

### 4.3 手动验证步骤

```plaintext
1. 复制 env.example 为 .env
2. 填写真实的 LLM 配置
3. 运行：python practice01/llm_client.py
4. 输入测试提示词
5. 检查输出是否符合预期格式
```

---

## 五、测试工具

| 工具 | 用途 |
| --- | --- |
| pytest | 单元测试框架 |
| unittest.mock | Mock 对象和函数 |
| requests-mock | Mock HTTP 请求（可选） |
| http.server | 简单的 Mock 服务（可选） |

---

## 六、测试输出验证

### 6.1 预期输出格式

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

### 6.2 验证要点

| 验证项 | 验证方法 |
| --- | --- |
| 模型名称 | 检查是否与配置一致 |
| Token 数值 | 检查是否为正整数 |
| 响应时间 | 检查是否大于 0 |
| 处理速度 | 检查计算是否正确（total_tokens / elapsed_time） |
| 响应内容 | 检查是否为非空字符串 |