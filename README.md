# AI智能体开发教学项目

基于Python的AI智能体开发教学项目，通过实践案例学习AI智能体的核心概念和实现方法。

## 项目结构

```
.
├── .gitignore          # Git忽略文件配置
├── env.example         # 环境变量配置模板
├── .env               # 环境变量配置文件（用户需自行创建）
└── practice01/        # 实践练习目录
    └── llm_client.py  # LLM客户端示例代码
```

## 环境配置

1. 复制 `env.example` 文件为 `.env`
2. 在 `.env` 文件中填写正确的LLM配置参数：
   - `BASE_URL`: API基础URL
   - `MODEL`: 模型名称
   - `API_KEY`: API密钥
   - `TEMPERATURE`: 温度参数 (0-1)
   - `MAX_TOKENS`: 最大token数

## 代码说明

### practice01/llm_client.py

**功能用途：**
- 读取项目根目录的 `.env` 配置文件
- 使用Python标准库 `http.client` 访问OpenAI兼容协议的LLM API
- 发送简单的问候消息并获取LLM响应
- 统计和显示API调用的性能指标：
  - Token消耗情况（prompt_tokens、completion_tokens、total_tokens）
  - 请求耗时（秒）
  - Token处理速度（tokens/second）

**实现的教学目标：**
1. **环境配置管理**：学习如何使用 `.env` 文件管理项目配置，理解环境变量的重要性
2. **HTTP客户端编程**：掌握使用Python标准库进行HTTP请求的方法，理解RESTful API调用
3. **LLM API集成**：学习OpenAI兼容协议的API调用方式，理解请求和响应格式
4. **性能监控**：学习如何统计和分析API调用的性能指标，理解token计费机制
5. **错误处理**：学习基本的异常处理和错误信息展示
6. **代码组织**：理解函数式编程的基本概念，学习代码模块化

**运行方式：**
```bash
python practice01/llm_client.py
```

**输出示例：**
```
=== LLM Call Results ===
Model: gpt-3.5-turbo
Prompt: Hello, how are you?
Response: I'm doing well, thank you for asking! How can I assist you today?

=== Token Usage ===
Prompt tokens: 10
Completion tokens: 15
Total tokens: 25

=== Performance ===
Time taken: 1.23 seconds
Tokens per second: 20.33
```

## 技术要点

### Python标准库使用
- `os`: 文件路径操作和环境变量处理
- `json`: JSON数据的序列化和反序列化
- `time`: 时间测量和性能统计
- `http.client`: HTTP客户端请求
- `urllib.parse`: URL解析和处理

### OpenAI兼容协议
- 请求格式：POST `/chat/completions`
- 认证方式：Bearer Token
- 响应格式：包含choices、usage等字段的JSON对象

### 性能优化考虑
- Token消耗统计：帮助理解API调用成本
- 时间测量：评估API响应速度
- 吞吐量计算：衡量处理效率

## 学习路径

1. **环境配置**：理解项目配置管理
2. **基础API调用**：掌握HTTP请求和响应处理
3. **性能监控**：学习性能指标统计和分析
4. **错误处理**：提高代码健壮性
5. **扩展应用**：基于基础代码开发更复杂的AI智能体功能

## 注意事项

- 确保 `.env` 文件包含正确的API密钥和配置
- 注意API调用的token消耗和成本控制
- 处理网络请求时考虑超时和重试机制
- 保护敏感信息，不要将 `.env` 文件提交到版本控制系统
