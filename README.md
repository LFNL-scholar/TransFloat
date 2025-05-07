# TransFloat - 实时语音翻译工具
![TransFloat 界面预览](/img/image.png)

TransFloat 是一个基于 PyQt6 和 DashScope API 开发的实时语音翻译工具，支持中英文双向翻译。它提供了一个简洁美观的用户界面，可以实时捕获音频并进行翻译。

## 功能特点

- 实时语音识别和翻译
- 支持中文 → 英文和英文 → 中文双向翻译
- 简洁现代的 macOS 风格界面
- 支持窗口拖动和快捷键操作
- 实时显示翻译结果，带有平滑动画效果
- 自动错误恢复和重试机制

## 系统要求

- Python 3.9 或更高版本
- macOS 系统（其他系统可能需要调整 UI 样式）
- 麦克风设备

## 安装说明

1. 克隆项目代码：
```bash
git clone [repository-url]
cd TransFloat
```

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 配置 DashScope API Key：
   - 在 `utils/config.py` 中设置你的 API Key
   - 或者设置环境变量：`export DASHSCOPE_API_KEY='your-api-key'`

## 使用方法

1. 启动程序：
```bash
python main.py
```

2. 界面操作：
   - 点击"切换方向"按钮可以在中英文翻译之间切换
   - 使用红色按钮关闭程序
   - 使用黄色按钮最小化窗口
   - 按 ESC 键可以快速退出程序
   - 可以通过拖动窗口标题栏移动窗口位置

## 项目结构

```
TransFloat/
├── main.py              # 主程序入口
├── ui/                  # UI 相关模块
│   ├── components.py    # UI 组件
│   ├── main_window.py   # 主窗口
│   └── __init__.py
├── translation/         # 翻译相关模块
│   ├── translator.py    # 翻译器核心
│   ├── callback.py      # 翻译回调处理
│   └── __init__.py
└── utils/              # 工具模块
    ├── config.py       # 配置文件
    └── __init__.py
```

## 依赖项

- PyQt6：用于构建图形界面
- dashscope：阿里云语音识别和翻译服务
- pyaudio：用于音频捕获和处理

## 常见问题

1. 切换翻译方向后无响应
   - 请等待 1-2 秒，系统需要重新初始化翻译服务
   - 确保网络连接正常

2. 无法识别声音
   - 检查麦克风权限是否已授权
   - 检查系统音频设置
   - 检查麦克风是否正常工作

3. API 错误
   - 确保已正确配置 DashScope API Key
   - 检查网络连接
   - 查看控制台错误信息

## 开发说明

### 添加新功能

1. UI 相关修改：
   - 在 `ui/components.py` 中添加新的组件
   - 在 `ui/main_window.py` 中集成新组件

2. 翻译功能修改：
   - 在 `translation/translator.py` 中修改翻译逻辑
   - 在 `translation/callback.py` 中处理新的回调事件

### 调试说明

- 程序会在控制台输出详细的日志信息
- 可以通过日志追踪翻译服务的状态
- 资源清理和重新初始化的过程都有日志记录

## 注意事项

1. API 密钥安全
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量或配置文件管理密钥

2. 资源管理
   - 程序会自动管理音频和翻译资源
   - 正常关闭程序以确保资源正确释放

3. 性能考虑
   - 翻译服务运行在独立线程中
   - 界面响应不会被翻译过程阻塞

## 许可证

[添加许可证信息]

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 联系方式

[lfnltech@163.com]

## 更新日志

### v1.0.0
- 初始版本发布
- 支持中英文双向翻译
- 实现基本的语音识别和翻译功能
