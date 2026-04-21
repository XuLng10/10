# AI智能体开发教学项目

基于Python的AI智能体开发教学项目，通过实践案例学习AI智能体的核心概念和实现方法。

## 项目结构

```
.
├── .gitignore          # Git忽略文件配置
├── env.example         # 环境变量配置模板
├── .env               # 环境变量配置文件（用户需自行创建）
├── practice01/        # 实践练习目录1
│   └── llm_client.py  # LLM客户端示例代码
├── practice02/        # 实践练习目录2
│   ├── terminal_chat.py  # 终端聊天示例代码
│   ├── tools.py         # 工具函数实现
│   └── tool_calling.py  # 工具调用功能实现
└── practice03/        # 实践练习目录3
    └── chat_summary.py  # 聊天记录总结功能
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

### practice02/terminal_chat.py

**功能用途：**
- 读取项目根目录的 `.env` 配置文件
- 实现终端交互式聊天界面
- 支持流式输出，实时显示LLM的回复
- 自动管理聊天历史，将历史对话添加到上下文
- 支持Ctrl+C退出终端
- 统计和显示API调用的性能指标

**实现的教学目标：**
1. **流式API调用**：学习如何使用流式输出获取LLM响应，提升用户体验
2. **交互式终端**：掌握终端输入输出的处理方法，实现用户友好的交互界面
3. **上下文管理**：学习如何维护和管理聊天历史，实现连续对话能力
4. **信号处理**：学习如何捕获和处理系统信号，实现优雅退出
5. **实时反馈**：理解流式输出的实现原理，提升用户体验
6. **循环控制**：掌握无限循环的实现和控制方法

**运行方式：**
```bash
python practice02/terminal_chat.py
```

**输出示例：**
```
=== Terminal Chat with LLM ===
Type your message and press Enter
Press Ctrl+C to exit

You: Hello, how are you?
Assistant: I'm doing well, thank you for asking! How can I assist you today?

=== Performance ===
Time taken: 1.56 seconds
Tokens used: 25
Tokens per second: 16.03

You: What can you help me with?
Assistant: I can help you with a wide range of topics, including:

1. Answering questions about various subjects
2. Providing information on current events
3. Assisting with writing and editing
4. Offering suggestions and recommendations
5. Helping with problem-solving
6. Teaching new concepts
7. Engaging in casual conversation

What would you like assistance with today?

=== Performance ===
Time taken: 2.34 seconds
Tokens used: 58
Tokens per second: 24.79

You: ^C
Exiting chat...
```

### practice02/tools.py

**功能用途：**
- 实现5个文件操作工具函数
- 提供文件系统操作的基础功能
- 为工具调用功能提供底层实现

**实现的工具函数：**
1. **list_files(directory)**：列出指定目录下的所有文件和目录，包括文件属性（大小、修改时间等）
2. **rename_file(directory, old_name, new_name)**：重命名指定目录下的文件
3. **delete_file(directory, file_name)**：删除指定目录下的文件
4. **create_file(directory, file_name, content)**：在指定目录下创建新文件并写入内容
5. **read_file(directory, file_name)**：读取指定目录下的文件内容
6. **curl(url)**：通过网络访问指定URL并返回网页内容

### practice02/tool_calling.py

**功能用途：**
- 实现基于LLM的工具调用功能
- 提供系统提示词，告知LLM可用的工具
- 处理LLM的工具调用请求并执行相应的工具函数
- 显示工具执行结果并获取LLM的总结
- 支持交互式终端聊天界面

**实现的教学目标：**
1. **工具调用机制**：学习如何设计和实现LLM的工具调用功能
2. **系统提示词设计**：掌握如何编写有效的系统提示词，指导LLM使用工具
3. **JSON解析与处理**：学习如何解析和处理LLM返回的JSON格式工具调用请求
4. **工具执行与结果处理**：掌握如何执行工具函数并处理其返回结果
5. **多轮对话管理**：学习如何在工具调用场景下管理多轮对话

**运行方式：**
```bash
python practice02/tool_calling.py
```

**输出示例：**
```
=== Tool Calling Chat with LLM ===
Type your message and press Enter
Press Ctrl+C to exit

Available tools:
1. list_files - List files in a directory
2. rename_file - Rename a file
3. delete_file - Delete a file
4. create_file - Create a new file with content
5. read_file - Read content of a file
6. curl - Access web page content

You: List files in the current directory
Assistant: {"toolcall": {"name": "list_files", "params": {"directory": "."}}}
Tool result: 目录: .git
目录: practice01
目录: practice02
文件: .gitignore | 大小: 59 | 修改时间: 2026-04-21 11:14:00
文件: README.md | 大小: 153 | 修改时间: 2026-04-21 11:47:00
文件: env.example | 大小: 18 | 修改时间: 2026-04-21 11:14:00
Assistant: I've listed the files in the current directory. You can see there are:
- Directories: .git, practice01, practice02
- Files: .gitignore, README.md, env.example

=== Performance ===
Time taken: 1.23 seconds
Tokens used: 45
Tokens per second: 36.60

You: Create a file named test.txt in the current directory with content "Hello, world!"
Assistant: {"toolcall": {"name": "create_file", "params": {"directory": ".", "file_name": "test.txt", "content": "Hello, world!"}}}
Tool result: 成功: 文件 'test.txt' 已创建并写入内容
Assistant: I've successfully created the file test.txt in the current directory with the content "Hello, world!".

=== Performance ===
Time taken: 1.56 seconds
Tokens used: 58
Tokens per second: 37.18

You: Access the Google homepage and show me the content
Assistant: {"toolcall": {"name": "curl", "params": {"url": "https://www.google.com"}}}
Tool result: <!DOCTYPE html><html lang="en">...</html>
Assistant: I've accessed the Google homepage. The content is an HTML document starting with the doctype declaration and containing the Google homepage structure.

=== Performance ===
Time taken: 2.34 seconds
Tokens used: 45
Tokens per second: 19.23
```

### practice03/chat_summary.py

**功能用途：**
- 实现聊天记录自动总结功能
- 当聊天历史超过5轮或上下文长度超过3k时，自动触发总结
- 对前70%的聊天内容进行压缩总结，保留最后30%的原文
- 支持交互式终端聊天界面
- 统计和显示API调用的性能指标

**实现的教学目标：**
1. **聊天历史管理**：学习如何管理和优化长对话的上下文
2. **自动总结机制**：掌握如何设计和实现聊天记录的自动总结功能
3. **上下文压缩**：学习如何通过总结来压缩长对话，减少token消耗
4. **性能优化**：理解如何通过总结机制提高对话效率和降低API成本
5. **智能触发条件**：学习如何设置合理的触发条件，自动执行总结操作

**运行方式：**
```bash
python practice03/chat_summary.py
```

**输出示例：**
```
=== 聊天记录总结功能演示 ===
Type your message and press Enter
Press Ctrl+C to exit

当聊天历史超过5轮或上下文长度超过3k时，会自动触发总结

You: Hello, how are you?
Assistant: I'm doing well, thank you for asking! How can I assist you today?

=== Performance ===
Time taken: 1.23 seconds
Tokens used: 25
Tokens per second: 20.33

You: What can you help me with?
Assistant: I can help you with a wide range of topics, including:

1. Answering questions about various subjects
2. Providing information on current events
3. Assisting with writing and editing
4. Offering suggestions and recommendations
5. Helping with problem-solving
6. Teaching new concepts
7. Engaging in casual conversation

What would you like assistance with today?

=== Performance ===
Time taken: 2.34 seconds
Tokens used: 58
Tokens per second: 24.79

# 多轮对话后...

⚠️  检测到聊天历史过长，开始总结...
=== 开始总结聊天记录 ===
总结完成，使用token: 45，耗时: 1.89秒
✅  总结完成，聊天历史已压缩

You: What's the weather like today?
Assistant: The user asked about the weather today. I should provide information about the current weather conditions.

=== Performance ===
Time taken: 1.56 seconds
Tokens used: 32
Tokens per second: 20.51
```

### practice03/chat_history_manager.py

**功能用途：**
- 实现聊天历史的关键信息提取和记录功能
- 每5次聊天自动提取关键信息，按照5W规则（Who、What、When、Where、Why）进行提取
- 将提取的关键信息记录到本地文件 `D:\chat-log\log.txt`（自动创建目录和文件）
- 支持聊天历史查找功能，通过 `/search` 命令或相关表达触发
- 支持交互式终端聊天界面
- 统计和显示API调用的性能指标

**实现的教学目标：**
1. **5W规则应用**：学习如何使用5W规则（Who、What、When、Where、Why）提取关键信息
2. **文件系统操作**：掌握如何创建目录、文件，以及进行增量写入
3. **自动触发机制**：学习如何设置基于聊天次数的自动触发条件
4. **聊天历史管理**：理解如何记录、存储和查询聊天历史
5. **命令解析**：学习如何解析用户命令并执行相应的操作
6. **上下文结合**：掌握如何将历史记录与用户请求结合，提供更准确的回复

**运行方式：**
```bash
python practice03/chat_history_manager.py
```

**输出示例：**
```
=== 聊天历史管理功能演示 ===
Type your message and press Enter
Press Ctrl+C to exit

功能说明：
1. 每5次聊天自动提取关键信息并记录到 D:\chat-log\log.txt
2. 输入以'/search'开头的消息可查找聊天历史
3. 表达'查找聊天历史'等意思也会触发历史查询

You: Hello, how are you?
Assistant: I'm doing well, thank you for asking! How can I assist you today?

=== Performance ===
Time taken: 1.23 seconds
Tokens used: 25
Tokens per second: 20.33

# 多轮对话后...

⚠️  检测到已进行5次聊天，开始提取关键信息...
=== 开始提取关键信息 ===
提取完成，使用token: 45，耗时: 1.89秒
创建日志目录: D:\chat-log
创建日志文件: D:\chat-log\log.txt
关键信息已记录到: D:\chat-log\log.txt
✅  关键信息提取和记录完成

You: /search What did we talk about earlier?
=== 查找聊天历史 ===
查找完成，使用token: 32，耗时: 1.56秒
Assistant: Based on the chat history, we discussed how I can help you with various topics including answering questions, providing information, assisting with writing, offering suggestions, helping with problem-solving, teaching new concepts, and engaging in casual conversation.

You: 查找聊天历史中关于天气的内容
=== 查找聊天历史 ===
查找完成，使用token: 28，耗时: 1.23秒
Assistant: I don't see any information about weather in the chat history.
```

## 技术要点

### Python标准库使用
- `os`: 文件路径操作和环境变量处理
- `json`: JSON数据的序列化和反序列化
- `time`: 时间测量和性能统计
- `http.client`: HTTP客户端请求
- `urllib.parse`: URL解析和处理
- `urllib.request`: 网络请求和网页内容获取
- `sys`: 系统相关操作和退出功能
- `signal`: 信号处理，用于捕获Ctrl+C等系统信号

### OpenAI兼容协议
- 请求格式：POST `/chat/completions`
- 认证方式：Bearer Token
- 响应格式：包含choices、usage等字段的JSON对象
- 流式输出：通过设置 `stream: true` 参数启用，响应为SSE（Server-Sent Events）格式

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
