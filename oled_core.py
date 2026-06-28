#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OLED 16x16 汉字取模核心逻辑"""

from __future__ import annotations

import os
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

FONT_SIZE = 16
CANVAS_SIZE = 16
BITMAP_BYTES = 32

SYSTEM_FONTS = [
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


@dataclass
class CharGlyph:
    index: int
    char: str
    utf8: list[int]
    gbk: list[int]
    bitmap: list[int]


def list_available_fonts() -> list[str]:
    fonts = [p for p in SYSTEM_FONTS if os.path.isfile(p)]
    local = os.path.join(os.path.dirname(__file__), "simhei.ttf")
    if os.path.isfile(local) and local not in fonts:
        fonts.insert(0, local)
    return fonts


def find_chinese_font() -> str:
    fonts = list_available_fonts()
    if fonts:
        return fonts[0]
    raise FileNotFoundError("未找到中文字体，请将 simhei.ttf 放到程序目录或安装系统字体")


def parse_chars(text: str, dedupe: bool = True) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for ch in text:
        if ch.isspace():
            continue
        if dedupe:
            if ch in seen:
                continue
            seen.add(ch)
        result.append(ch)
    return result


def render_char_bitmap(char: str, font_path: str) -> list[int]:
    """逐行式、从左到右、高位在前（阴码）"""
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
    bitmap: list[int] = []
    for row in range(CANVAS_SIZE):
        for byte_col in range(2):
            byte_val = 0
            for bit in range(8):
                col = byte_col * 8 + bit
                if pixels[col, row]:
                    byte_val |= 1 << (7 - bit)
            bitmap.append(byte_val)
    return bitmap


def bitmap_to_image(
    bitmap: list[int],
    scale: int = 10,
    on_color: tuple[int, int, int] = (0, 212, 170),
    off_color: tuple[int, int, int] = (13, 17, 23),
) -> Image.Image:
    img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), off_color)
    pixels = img.load()
    for row in range(CANVAS_SIZE):
        for byte_col in range(2):
            byte_val = bitmap[row * 2 + byte_col]
            for bit in range(8):
                col = byte_col * 8 + bit
                if byte_val & (1 << (7 - bit)):
                    pixels[col, row] = on_color
    size = CANVAS_SIZE * scale
    return img.resize((size, size), Image.Resampling.NEAREST)


def format_hex(values: list[int]) -> str:
    return ",".join(f"0x{v:02x}" for v in values)


def build_glyph(char: str, index: int, font_path: str) -> tuple[CharGlyph | None, str | None]:
    utf8 = list(char.encode("utf-8"))
    if len(utf8) != 3:
        return None, f"字符 '{char}' 的 UTF-8 编码不是 3 字节，已跳过"

    try:
        gbk = list(char.encode("gbk"))
    except UnicodeEncodeError:
        return None, f"字符 '{char}' 无法转换为 GBK，已跳过"

    if len(gbk) != 2:
        return None, f"字符 '{char}' 的 GBK 编码不是 2 字节，已跳过"

    bitmap = render_char_bitmap(char, font_path)
    return CharGlyph(index=index, char=char, utf8=utf8, gbk=gbk, bitmap=bitmap), None


def generate_glyphs(
    text: str, font_path: str, dedupe: bool = True
) -> tuple[list[CharGlyph], list[str]]:
    chars = parse_chars(text, dedupe=dedupe)
    glyphs: list[CharGlyph] = []
    warnings: list[str] = []

    for char in chars:
        glyph, warning = build_glyph(char, len(glyphs), font_path)
        if warning:
            warnings.append(warning)
        elif glyph:
            glyphs.append(glyph)

    return glyphs, warnings


def glyphs_to_c_code(glyphs: list[CharGlyph]) -> str:
    if not glyphs:
        return ""

    lines_zh = ["const u8 zh16x16[][36]={"]
    lines_gbk = ["", "const u8 zh16x16_gbk[][2]={"]

    for g in glyphs:
        row_data = g.utf8 + [0x00] + g.bitmap
        lines_zh.append(f"/* {g.index} {g.char} */{{{format_hex(row_data)}}},")
        lines_gbk.append(f"{{{format_hex(g.gbk)}}}, /* {g.char} */")

    lines_zh.append("};")
    lines_gbk.append("};")
    return "\n".join(lines_zh + lines_gbk)


def generate_c_code(text: str, font_path: str, dedupe: bool = True) -> str:
    glyphs, _ = generate_glyphs(text, font_path, dedupe=dedupe)
    return glyphs_to_c_code(glyphs)
