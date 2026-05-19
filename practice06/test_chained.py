import sys
import os
sys.path.insert(0, 'practice06')

from tool_client import (
    load_env_file,
    execute_chained_tool_call,
    ChainedCallContext,
    build_analysis_prompt,
    extract_json_from_response,
    parse_llm_response,
    execute_tool,
    file_search,
    read_file,
    write_file,
    web_fetch
)


def test_basic_functions():
    """测试基础工具函数"""
    print("=== 测试基础工具函数 ===")
    
    print("\n1. 测试 file_search")
    result = file_search("def", "practice05")
    print(f"搜索结果: {result}")
    
    print("\n2. 测试 read_file")
    result = read_file("1.txt")
    print(f"读取结果: {result}")
    
    print("\n3. 测试 read_file 2.txt")
    result = read_file("2.txt")
    print(f"读取结果: {result}")
    
    print("\n4. 测试 write_file")
    result = write_file("practice06/test_output.txt", "测试内容")
    print(f"写入结果: {result}")
    
    print("\n5. 测试 ChainedCallContext")
    ctx = ChainedCallContext(max_iterations=5)
    ctx.add_step("test_tool", {"param": "value"}, "result")
    ctx.set_variable("test_var", "test_value")
    print(f"步骤数: {len(ctx.steps)}")
    print(f"变量: {ctx.variables}")
    print(f"最后结果: {ctx.get_last_result()}")
    print(f"步骤摘要: {ctx.get_steps_summary()}")
    
    print("\n6. 测试 extract_json_from_response")
    test_cases = [
        '{"done": true, "answer": "test"}',
        '```json{"done": false, "tool_call": {"name": "test", "arguments": {"param": "val"}}}```',
        '普通文本'
    ]
    for tc in test_cases:
        result = extract_json_from_response(tc)
        print(f"  {tc[:40]}... -> {result}")
    
    print("\n7. 测试 build_analysis_prompt")
    ctx2 = ChainedCallContext(max_iterations=10)
    prompt = build_analysis_prompt("测试请求", ctx2)
    print(f"提示词长度: {len(prompt)}")
    print(f"提示词前200字符:\n{prompt[:200]}...")
    
    print("\n8. 测试 execute_tool")
    result = execute_tool("read_file", {"file_path": "1.txt"})
    print(f"执行工具结果: {result}")
    
    print("\n=== 基础功能测试完成 ===")


if __name__ == "__main__":
    test_basic_functions()