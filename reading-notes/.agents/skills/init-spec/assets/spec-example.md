# LLM API 客户端工具 - 规格说明

## 1. 需求概述

创建支持 OpenAI 兼容协议的 LLM API 客户端，提供 token 消耗统计、响应时间和处理速度指标。

## 2. 文件结构

```
Prompt/
├── env.example          # 配置模板
├── .env                 # 用户配置（手动创建）
└── practice01/
    └── llm_client.py    # LLM 客户端
```

## 3. 配置参数

| 参数 | 说明 |
| --- | --- |
| LLM_BASE_URL | OpenAI 兼容 API 地址 |
| LLM_MODEL | 模型名称 |
| LLM_API_KEY | API 令牌 |

## 4. 核心功能

1. 读取 `.env` 配置
2. HTTP POST 调用 LLM API
3. 统计：token 消耗、响应时间、token/s 速度

## 5. 输出格式

```
模型: xxx
总 Token: xxx
响应时间: xxxs
处理速度: xxx token/s
响应内容: xxx
```