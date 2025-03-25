"""
Token统计工具模块 - 增强版
"""
import re
from collections import defaultdict

class TokenCounter:
    def __init__(self):
        self.input_stats = defaultdict(int)  # 输入token统计
        self.output_stats = defaultdict(int)  # 输出token统计
        self.total_input = 0
        self.total_output = 0
    
    def count_input_tokens(self, text, model_type="gpt"):
        """统计输入token"""
        if model_type == "gpt":
            tokens = len(text) / 4  # GPT估算
        elif model_type == "claude":
            tokens = len(text) / 3  # Claude估算
        else:
            tokens = len(text)  # 默认字符数
        
        self.input_stats[model_type] += tokens
        self.total_input += tokens
        return round(tokens, 2)
    
    def count_output_tokens(self, text, model_type="gpt"):
        """统计输出token"""
        tokens = len(text) / 4  # 默认使用GPT估算
        self.output_stats[model_type] += tokens
        self.total_output += tokens
        return round(tokens, 2)
    
    def get_stats(self):
        """获取详细统计结果"""
        return {
            "total_input": round(self.total_input, 2),
            "total_output": round(self.total_output, 2),
            "input_by_model": dict(self.input_stats),
            "output_by_model": dict(self.output_stats)
        }

def init_counter():
    """初始化计数器"""
    return TokenCounter()

def process_input_text(counter, text, model_type="gpt"):
    """处理输入文本并统计token"""
    return counter.count_input_tokens(text, model_type)

def process_output_file(counter, file_path, model_type="gpt"):
    """处理输出文件并统计token"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            output_text = f.read()
            if output_text:
                return counter.count_output_tokens(output_text, model_type)
            return 0
    except Exception as e:
        print(f"统计输出token时出错: {e}")
        return 0

def generate_report(counter):
    """生成详细统计报告"""
    stats = counter.get_stats()
    report = f"""
    Token详细统计报告
    ================
    总输入Token数: {stats['total_input']}
    总输出Token数: {stats['total_output']}
    总Token消耗: {round(stats['total_input'] + stats['total_output'], 2)}
    
    输入Token统计:
    """
    for model, count in stats['input_by_model'].items():
        report += f"  {model.upper()}模型: {count}\n"
    
    report += "\n    输出Token统计:\n"
    for model, count in stats['output_by_model'].items():
        report += f"  {model.upper()}模型: {count}\n"
    
    return report
