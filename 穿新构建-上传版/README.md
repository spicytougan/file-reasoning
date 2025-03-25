# 文件推理工具 (v2.1)

## 项目简介

这是一个基于Python的文本处理工具，主要功能包括：
- 批量处理文本文件
- 自动检测文件编码
- 支持大文件分块处理
- 自动重试失败请求
- 实时显示处理进度
- 多文件并发处理
- 智能API并发控制
- 图形化用户界面
- Token使用统计

## 主要功能

1. **文件处理**
   - 支持多种文件格式
   - 自动检测文件编码
   - 大文件分块处理
   - 多文件并发处理

2. **API集成**
   - 支持Deepseek API
   - 智能并发控制
   - 自动重试机制
   - 请求队列管理

3. **用户界面**
   - 文件选择对话框
   - 系统提示词管理
   - 实时处理进度显示
   - 一键停止推理

4. **统计功能**
   - Token使用统计
   - 处理结果报告
   - 性能分析

## 快速开始

### 克隆库
```bash
git clone https://github.com/spicytougan/file-reasoning.git
```
### 安装依赖
```bash
pip install requests chardet
```

### 配置说明
1. 编辑`config.json`设置API参数
2. 在`status_codes.json`中添加状态码说明

### 运行程序
```bash
python main.py
```

## 文件结构

```
.
├── main.py            # 主程序
├── api.py             # API请求模块
├── config.json        # API配置
├── status_codes.json  # HTTP状态码说明
├── token_utils.py     # Token统计工具
├── prompt_history.json # 提示词历史记录
└── README.md          # 说明文档
```

## 使用建议

1. 大文件处理时请耐心等待
2. 可随时使用"停止推理"按钮中断处理
3. 输出文件会自动保存在原目录下
4. 使用Deepseek API可获得更高并发性能
5. 多文件处理时会自动平衡负载

## 并发处理说明

- 默认并发数: 2 (适用于大多数API)
- Deepseek API并发数: 10
- 每个文件会被自动分块处理
- 系统会自动管理并发请求队列
