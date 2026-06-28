#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STM32 OLED 汉字 16x16 取模工具 - 输出 C 语言字模数组"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    sys.exit(1)


FONT_SIZE = 16
CANVAS_SIZE = 16
BITMAP_BYTES = 32  # 16x16 / 8


def find_chinese_font() -> str:
    """查找系统中可用的中文字体"""
    candidates = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\STSONG.TTF",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "未找到中文字体，请将 simhei.ttf 放到程序目录或安装系统字体"
    )


def render_char_bitmap(char: str, font_path: str) -> list[int]:
    """
    渲染单个汉字为 16x16 点阵，逐行式、从左到右、高位在前（阴码）。
    返回 32 字节的位图数据。
    """
    font = ImageFont.truetype(font_path, FONT_SIZE)
    img = Image.new("1", (CANVAS_SIZE, CANVAS_SIZE), 0)
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (CANVAS_SIZE - tw) // 2 - bbox[0]
    y = (CANVAS_SIZE - th) // 2 - bbox[1]
    draw.text((x, y), char, font=font, fill=1)

    pixels = img.load()
    bitmap = []
    for row in range(CANVAS_SIZE):
        for byte_col in range(2):
            byte_val = 0
            for bit in range(8):
                col = byte_col * 8 + bit
                if pixels[col, row]:
                    byte_val |= 1 << (7 - bit)
            bitmap.append(byte_val)
    return bitmap


def char_to_utf8_bytes(char: str) -> list[int]:
    return list(char.encode("utf-8"))


def char_to_gbk_bytes(char: str) -> list[int]:
    return list(char.encode("gbk"))


def format_hex(values: list[int]) -> str:
    return ",".join(f"0x{v:02x}" for v in values)


def generate_c_code(chars: str, font_path: str) -> str:
    """根据输入汉字生成 C 语言字模代码"""
    seen = set()
    unique_chars = []
    for ch in chars:
        if ch.strip() == "" or ch.isspace():
            continue
        if ch not in seen:
            seen.add(ch)
            unique_chars.append(ch)

    if not unique_chars:
        return ""

    lines_zh = ["const u8 zh16x16[][36]={"]
    lines_gbk = ["", "const u8 zh16x16_gbk[][2]={"]

    for idx, char in enumerate(unique_chars):
        utf8 = char_to_utf8_bytes(char)
        if len(utf8) != 3:
            print(f"警告: 字符 '{char}' 的 UTF-8 编码不是 3 字节，已跳过")
            continue

        try:
            gbk = char_to_gbk_bytes(char)
        except UnicodeEncodeError:
            print(f"警告: 字符 '{char}' 无法转换为 GBK，已跳过")
            continue

        if len(gbk) != 2:
            print(f"警告: 字符 '{char}' 的 GBK 编码不是 2 字节，已跳过")
            continue

        bitmap = render_char_bitmap(char, font_path)
        row_data = utf8 + [0x00] + bitmap

        lines_zh.append(f"/* {idx} {char} */{{{format_hex(row_data)}}},")
        lines_gbk.append(f"{{{format_hex(gbk)}}}, /* {char} */")

    lines_zh.append("};")
    lines_gbk.append("};")

    return "\n".join(lines_zh + lines_gbk)


def main():
    print("=" * 50)
    print("  STM32 OLED 汉字 16x16 取模工具")
    print("  输出格式: zh16x16 + zh16x16_gbk")
    print("=" * 50)

    try:
        font_path = find_chinese_font()
        print(f"使用字体: {font_path}\n")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    while True:
        try:
            text = input("请输入汉字（直接回车退出）: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not text:
            print("再见!")
            break

        code = generate_c_code(text, font_path)
        if code:
            print("\n" + code + "\n")
        else:
            print("未生成有效字模，请检查输入。\n")


if __name__ == "__main__":
    main()
