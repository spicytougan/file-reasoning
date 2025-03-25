import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "deepseek-ai/DeepSeek-V3",
    "stream": True,
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "messages": [
        {
            "content": "你是优化专家",
            "role": "system"
        },
        {
            "content": "你好，你能做什么?",
            "role": "user"
        }
    ]
}
headers = {
    "Authorization": "Bearer sk-ynadlndkdnemdyoxfvcfwkabtwbbomgktsglnccwdnpvayzr",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)