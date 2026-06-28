# STM32 OLED Studio

面向嵌入式开发的 **OLED 16×16 汉字取模工具**。输入汉字，一键生成 STM32 可直接使用的 C 语言字模数组，并提供可视化点阵预览。

## 功能特性

- **桌面 GUI**：深色嵌入式工程风格界面，操作直观
- **16×16 点阵取模**：阴码 · 逐行式 · 高位在前（兼容常见 PCtoLCD 设置）
- **双编码输出**：同时生成 UTF-8 字模与 GBK 对照表
- **实时预览**：网格卡片 + 放大点阵，显示 UTF-8 / GBK 编码
- **一键导出**：复制 C 代码或保存为 `.h` 头文件
- **字体可选**：支持系统黑体/宋体/雅黑，也可自定义 `.ttf` 字体

## 输出格式

```c
const u8 zh16x16[][36]={
/* 0 波 */{0xe6,0xb3,0xa2,0x00, /* 32 字节点阵 */ ...},
};

const u8 zh16x16_gbk[][2]={
{0xb2,0xa8}, /* 波 */
};
```

| 数组 | 每行字节 | 说明 |
|------|----------|------|
| `zh16x16` | 36 | UTF-8 (3) + `0x00` + 点阵 (32) |
| `zh16x16_gbk` | 2 | GBK 编码，用于快速索引 |

## 环境要求

- Python 3.10+
- Windows / macOS / Linux
- 系统中文字体（Windows 自带黑体/宋体即可）

## 安装与运行

```bash
# 克隆项目
git clone https://github.com/sank889/STM32-OLED-Studio.git
cd STM32-OLED-Studio

# 安装依赖
py -m pip install -r requirements.txt

# 启动
py main.py
```

Windows 用户也可双击 `install.bat` 安装依赖，双击 `run.bat` 启动程序。

> 若 `pip` 命令报错，请使用 `py -m pip` 代替。

## 使用说明

1. 在左侧 **INPUT** 区域输入汉字字符串
2. 选择渲染字体（可选），勾选是否自动去重
3. 点击 **生成字模**
4. 在中间 **PREVIEW** 区域点击字符，查看点阵与编码
5. 在右侧 **OUTPUT** 区域复制代码或保存为 `.h` 文件

## 项目结构

```
STM32-OLED-Studio/
├── main.py           # 桌面 UI 入口
├── oled_core.py      # 取模核心逻辑
├── requirements.txt  # Python 依赖
├── install.bat       # Windows 依赖安装脚本
├── run.bat           # Windows 启动脚本
└── README.md
```

## 技术栈

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — 现代深色 GUI
- [Pillow](https://python-pillow.org/) — 字体渲染与点阵生成

## License

MIT
