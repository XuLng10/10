# AI智能体开发教学项目

这是一个基于Python的AI智能体开发教学项目，旨在帮助学习者掌握AI智能体开发的核心技能。

## 项目结构

```
.
├── .env.example          # 环境变量配置模板
├── .env                  # 环境变量配置文件（需从模板复制）
├── .gitignore            # Git忽略文件
├── venv/                 # Python虚拟环境
├── practice01/           # 练习1：LLM API调用
│   └── llm_api_test.py   # LLM API调用测试脚本
└── README.md             # 项目说明文档
```

## 环境配置

### 1. 激活虚拟环境

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 配置LLM服务

复制环境变量模板并配置：

```bash
# 复制模板
copy env.example .env

# 编辑.env文件，填入正确的LLM配置
# - LLM_BASE_URL: LLM服务地址
# - LLM_MODEL: 模型名称
# - LLM_API_KEY: API密钥
```

## 练习代码说明

### practice01/llm_api_test.py

**功能用途：**
- 使用Python标准库`http.client`调用OpenAI兼容协议的LLM API
- 实现Token消耗统计、请求耗时统计、处理速度计算
- 支持HTTP和HTTPS协议自动切换

**教学目标：**
1. 学习如何手动解析.env环境变量文件
2. 掌握使用Python标准库进行HTTP/HTTPS请求
3. 理解OpenAI API的请求格式和响应结构
4. 学习如何统计API调用的关键指标（Token数、耗时、速度）
5. 了解错误处理和异常捕获的最佳实践

**运行方式：**

```bash
python practice01/llm_api_test.py
```

**输出示例：**

```
============================================================
LLM API调用测试 - Token消耗统计
============================================================

配置信息:
  Base URL: http://localhost:1234/v1
  Model: 111
  Timeout: 60s

发送请求:
  Messages: [{"role": "user", "content": "请用一句话介绍Python编程语言的特点。"}]

响应内容:
  Python是一种简洁优雅、可读性强的高级编程语言，支持多种编程范式。

统计信息:
  总耗时: 1.234秒
  输入Token数: 28
  输出Token数: 35
  总Token数: 63
  处理速度: 51.05 tokens/s

============================================================
调用成功！
============================================================
```

## Git操作指南

### 首次配置（仅需一次）

```bash
# 配置用户名
git config --global user.name "Your Name"

# 配置邮箱
git config --global user.email "your.email@example.com"
```

### 初始化仓库并提交

1. 在开发平台的代码git管理面板中点击"初始化仓库"
2. 点击自动按钮，自动生成变更信息
3. 提交代码到仓库

## 学习路径

1. **基础篇**：掌握LLM API调用、环境变量管理、HTTP请求
2. **进阶篇**：学习API封装、错误处理、性能优化
3. **实战篇**：构建完整的AI智能体应用

## 注意事项

- 请勿将`.env`文件提交到Git仓库（已在.gitignore中配置）
- 确保LLM服务已正确启动并可访问
- 建议在虚拟环境中运行代码，避免依赖冲突

## License

MIT License