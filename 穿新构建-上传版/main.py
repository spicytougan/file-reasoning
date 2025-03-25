import tkinter as tk
from tkinter import filedialog, ttk
import requests
import json
import chardet
from token_utils import init_counter, process_input_text, process_output_file, generate_report

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
import random

# 全局变量
stop_inference = False
prompt_var = None  # 初始化全局变量
token_counter = init_counter()  # 初始化token计数器

def create_gui():
    global prompt_var  # 声明使用全局变量
    root = tk.Tk()
    root.title("文件推理工具")
    
    # 提示词输入框
    prompt_frame = tk.Frame(root)
    prompt_frame.pack(pady=10)
    
    tk.Label(prompt_frame, text="系统提示词:").pack(side=tk.LEFT)
    
    # 历史提示词下拉菜单
    prompt_var = tk.StringVar(root)
    prompt_dropdown = ttk.Combobox(prompt_frame, textvariable=prompt_var, width=47)
    prompt_dropdown.pack(side=tk.LEFT, padx=5)
    
    # 加载历史提示词
    try:
        with open('prompt_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)['history']
            prompt_dropdown['values'] = history
            if history:
                prompt_var.set(history[0])
    except:
        pass
    
    # 直接输入提示词的文本框
    prompt_entry = tk.Entry(prompt_frame, width=50)
    prompt_entry.insert(0, "你是数学专家和老师，用中文来讲解这些课程或对话中提到的数学问题。")  # 默认提示词
    prompt_entry.pack(side=tk.LEFT, padx=5)
    
    # 按钮框架
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    # 文件选择按钮
    start_button = tk.Button(button_frame, text="选择文件并开始推理", command=select_files)
    start_button.pack(side=tk.LEFT, padx=5)
    
    # 停止按钮
    stop_button = tk.Button(button_frame, text="停止推理", command=stop_inference_process)
    stop_button.pack(side=tk.LEFT, padx=5)
    
    # Token统计按钮
    stats_button = tk.Button(button_frame, text="显示Token统计", command=show_token_stats)
    stats_button.pack(side=tk.LEFT, padx=5)
    
    # 将提示词相关变量作为全局变量
    global system_prompt_entry
    system_prompt_entry = prompt_entry
    
    root.mainloop()

def show_token_stats():
    """显示token统计信息"""
    stats = generate_report(token_counter)
    print("\n" + "="*40)
    print(stats)
    print("="*40 + "\n")

def stop_inference_process():
    global stop_inference
    stop_inference = True
    print("推理过程已停止")

def select_files():
    global stop_inference
    stop_inference = False  # 重置停止标志
    
    # 获取用户输入的系统提示词
    system_prompt = prompt_var.get() or system_prompt_entry.get()
    
    # 保存到历史记录
    if system_prompt:
        try:
            with open('prompt_history.json', 'r+', encoding='utf-8') as f:
                data = json.load(f)
                history = data['history']
                if system_prompt in history:
                    history.remove(system_prompt)
                history.insert(0, system_prompt)
                data['history'] = history[:10]  # 最多保留10条
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()
        except Exception as e:
            print(f"保存提示词历史失败: {e}")
    
    file_paths = filedialog.askopenfilenames(title="选择文件", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if not file_paths:
        print("未选择文件。")
        return

    print(f"已选择 {len(file_paths)} 个文件。")
    total_files = len(file_paths)
    
    # 根据API URL设置并发数
    if "deepseek.com" in config["api_url"]:
        max_workers = 10  # Deepseek API不限制并发
    else:
        max_workers = 2  # 其他API保持低并发
    retry_attempts = 3  # Number of retry attempts per chunk
    retry_delay = 5  # Delay between retries in seconds
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 处理所有文件
        futures = []
        for file_path in file_paths:
            try:
                with open(file_path, 'rb') as f:
                    rawdata = f.read()
                    result = chardet.detect(rawdata)
                    encoding = result['encoding']
                    confidence = result['confidence']
                    print(f"检测到编码: {encoding}, 置信度: {confidence}")

                if encoding is None:
                    encodings_to_try = ['utf-8', 'gbk', 'Windows-1252']
                    for enc in encodings_to_try:
                        try:
                            with open(file_path, 'r', encoding=enc) as file:
                                text = file.read()
                                break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            print(f"读取文件时出错: {e}")
                            continue
                    else:
                        print("无法使用任何尝试的编码解码文件。")
                        continue
                else:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            text = file.read()
                    except Exception as e:
                        print(f"读取文件时出错: {e}")
                        continue

                # 统计输入token
                model_type = "gpt" if "openai" in config["api_url"] else "claude" if "anthropic" in config["api_url"] else "default"
                input_tokens = process_input_text(token_counter, text, model_type)
                print(f"文件 {file_path} 输入估算token数: {input_tokens}")

                # Split text into chunks of max context size
                chunk_size = config["model_config"]["max_context"]
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                print(f"文件 {file_path} 内容被分割为 {len(chunks)} 个块进行推理")
                
                # 为每个文件的分块创建任务
                for chunk_num, chunk_text in enumerate(chunks, start=1):
                    futures.append(executor.submit(
                        infer_with_retry, 
                        chunk_text, 
                        file_path, 
                        chunk_num, 
                        retry_attempts, 
                        retry_delay, 
                        system_prompt
                    ))

            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
                continue
        
        # 处理所有任务
        for i, future in enumerate(as_completed(futures), start=1):
            if stop_inference:
                print("推理过程被用户中断")
                break
            try:
                future.result()
                print(f"已完成 {i}/{len(futures)} 个任务")
            except Exception as e:
                print(f"处理任务时出错: {e}")

        # 显示最终token统计
        show_token_stats()

def infer(text, file_path, chunk_num=1, delay=None, system_prompt="你是优化专家"):
    """
    Perform inference on a chunk of text.
    Optionally add a delay before the request.
    """
    if delay:
        sleep(delay)

    url = config["api_url"]
    payload = {
        "model": config["model_name"],
        "stream": True,
        "max_tokens": config["model_config"]["max_tokens"],
        "temperature": config["model_config"]["temperature"],
        "top_p": config["model_config"]["top_p"],
        "top_k": config["model_config"]["top_k"],
        "frequency_penalty": config["model_config"]["frequency_penalty"],
        "n": 1,
        "messages": [
            {
                "content": system_prompt,
                "role": "system"
            },
            {
                "content": text,
                "role": "user"
            }
        ],
        "response_format": {"type": config["model_config"]["response_format"]}
    }
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    try:
        # 计算输入文本的token数
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(config["model_name"])
            token_count = len(encoding.encode(text))
        except ImportError:
            # 如果tiktoken未安装，使用字符数作为近似值
            token_count = len(text)
            print(f"正在发送API请求，输入文本长度: {token_count} 字符...")
        except Exception as e:
            token_count = len(text)
            print(f"正在发送API请求，输入文本长度: {token_count} 字符...")
        else:
            print(f"正在发送API请求，输入文本长度: {token_count} tokens...")
        response = requests.request("POST", url, json=payload, headers=headers, stream=True, timeout=30)
        # 从status_codes.json读取状态码含义
        try:
            with open('status_codes.json', 'r', encoding='utf-8') as f:
                status_codes = json.load(f)
            meaning = status_codes.get(str(response.status_code), "未知状态码")
        except Exception as e:
            meaning = "未知状态码"
        print(f"API响应状态码: {response.status_code} ({meaning})")
        buffer = ""
        first_chunk = True
        output_file = f"{file_path}.output.txt"
        mode = 'a' if chunk_num > 1 else 'w'  # Append if not first chunk
        with open(output_file, mode, encoding='utf-8') as f:
            if chunk_num > 1:
                f.write("\n\n")  # Add separator between chunks
            for chunk in response.iter_content(chunk_size=None):
                decoded_chunk = chunk.decode('utf-8')
                buffer += decoded_chunk
                for line in buffer.splitlines():
                    if line.startswith("data: "):
                        line = line[6:]
                    try:
                        data = json.loads(line)
                        if 'choices' not in data or len(data['choices']) == 0:
                            print(f"API返回的响应缺少 'choices' 字段: {data}")
                            return
                        delta = data['choices'][0]['delta']

                        if first_chunk:
                            if 'role' in delta and delta['role'] == 'assistant':
                                f.write("<assistant>")
                                print("<assistant>", end="", flush=True)
                            first_chunk = False

                        # 根据响应判断是否为推理模型
                        is_reasoner = 'reasoning_content' in delta
                        
                        # 处理推理模型的响应
                        if is_reasoner:
                            # 同时处理reasoning_content和content
                            reasoning_content = delta.get('reasoning_content', '')
                            content = delta.get('content', '')
                            if reasoning_content:
                                f.write(str(reasoning_content))
                                print(str(reasoning_content), end="", flush=True)
                            if content:
                                f.write(str(content))
                                print(str(content), end="", flush=True)
                        else:
                            # 处理普通模型的响应
                            content = delta.get('content', '')
                            if content:
                                f.write(str(content))
                                print(str(content), end="", flush=True)

                        buffer = ""
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"处理过程中发生错误: {e}")
                        print(f"API返回的原始数据: {line}")
                        return
            f.write("</assistant>")
            print("</assistant>")
        
        # 确保文件已关闭
        f.flush()
        f.close()
        
        # 统计输出token
        output_tokens = process_output_file(token_counter, output_file, model_type)
        if output_tokens > 0:
            print(f"输出结果估算token数: {output_tokens}")
        
        print(f"推理结果已保存到: {output_file}")
        # 自动打开生成的文件
        try:
            import os
            os.startfile(output_file)
        except Exception as e:
            print(f"无法自动打开文件: {e}")

    except requests.exceptions.ConnectionError as e:
        raise Exception(f"网络连接错误: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API请求失败: {e}")

def infer_with_retry(text, file_path, chunk_num, retry_attempts=3, retry_delay=5, system_prompt="你是优化专家"):
    """
    Perform inference with retry logic.
    """
    for attempt in range(retry_attempts):
        try:
            # Add random jitter to delay to avoid synchronized retries
            delay = retry_delay * (1 + random.random()) if attempt > 0 else None
            return infer(text, file_path, chunk_num, delay, system_prompt)
        except Exception as e:
            if attempt == retry_attempts - 1:
                raise e
            print(f"第 {chunk_num} 个块第 {attempt + 1} 次尝试失败: {e}")
            print(f"等待 {retry_delay} 秒后重试...")
            sleep(retry_delay)

# 启动GUI
create_gui()
