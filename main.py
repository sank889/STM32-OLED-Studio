
"""STM32 OLED Studio - 16x16 汉字取模桌面工具"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
    from PIL import ImageTk
except ImportError:
    print("请先安装依赖: py -m pip install -r requirements.txt")
    sys.exit(1)

from oled_core import (
    CharGlyph,
    bitmap_to_image,
    find_chinese_font,
    generate_glyphs,
    glyphs_to_c_code,
    list_available_fonts,
)

C = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "panel2": "#1c2128",
    "border": "#30363d",
    "accent": "#00d4aa",
    "accent_dim": "#0a4d3c",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "code": "#7ee787",
    "warn": "#f0883e",
    "header": "#58a6ff",
}


class GlyphCard(ctk.CTkFrame):
    """单个汉字的点阵预览卡片"""

    def __init__(self, master, glyph: CharGlyph, font_path: str, on_select, **kwargs):
        super().__init__(master, fg_color=C["panel2"], corner_radius=6, **kwargs)
        self.glyph = glyph
        self.on_select = on_select
        self._selected = False

        self.configure(border_width=1, border_color=C["border"])

        ctk.CTkLabel(
            self,
            text=f"[{glyph.index}] {glyph.char}",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=C["muted"],
        ).pack(pady=(6, 2))

        preview = bitmap_to_image(glyph.bitmap, scale=6)
        self._photo = ImageTk.PhotoImage(preview)
        self._img_label = tk.Label(
            self, image=self._photo, bg=C["panel2"], cursor="hand2"
        )
        self._img_label.pack(padx=8, pady=4)
        self._img_label.bind("<Button-1>", lambda _e: self.on_select(glyph))

        for w in (self, self._img_label):
            w.bind("<Button-1>", lambda _e: self.on_select(glyph))

    def set_selected(self, selected: bool):
        self._selected = selected
        self.configure(border_color=C["accent"] if selected else C["border"])


class OLEDStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STM32 OLED Studio")
        self.geometry("1100x720")
        self.minsize(960, 600)
        self.configure(fg_color=C["bg"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.font_path = self._init_font()
        self.glyphs: list[CharGlyph] = []
        self._selected_glyph: CharGlyph | None = None
        self._preview_photo = None
        self._card_widgets: list[GlyphCard] = []

        self._build_ui()
        self._set_status(f"就绪  |  字体: {os.path.basename(self.font_path)}")

    def _init_font(self) -> str:
        try:
            return find_chinese_font()
        except FileNotFoundError:
            return ""

    def _build_ui(self):
        self._build_header()
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        body.grid_columnconfigure(0, weight=0, minsize=260)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_input_panel(body)
        self._build_preview_panel(body)
        self._build_output_panel(body)
        self._build_statusbar()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            left,
            text="STM32 OLED Studio",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=C["header"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="16×16 汉字取模  ·  阴码  ·  逐行式  ·  高位在前",
            font=ctk.CTkFont(size=12),
            text_color=C["muted"],
        ).pack(anchor="w")

        badge = ctk.CTkFrame(hdr, fg_color=C["accent_dim"], corner_radius=4)
        badge.pack(side="right", padx=20, pady=14)
        ctk.CTkLabel(
            badge,
            text="  zh16x16[36] + zh16x16_gbk[2]  ",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["accent"],
        ).pack(padx=6, pady=2)

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent, fg_color=C["panel"], corner_radius=8, border_width=1, border_color=C["border"]
        )
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=C["accent"],
        ).pack(anchor="w", padx=12, pady=(10, 4))
        return frame

    def _build_input_panel(self, parent):
        panel = self._section(parent, "// INPUT")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        ctk.CTkLabel(inner, text="汉字字符串", text_color=C["muted"], font=ctk.CTkFont(size=12)).pack(
            anchor="w"
        )
        self.input_text = ctk.CTkTextbox(
            inner,
            height=100,
            font=ctk.CTkFont(size=14),
            fg_color=C["bg"],
            border_color=C["border"],
            border_width=1,
        )
        self.input_text.pack(fill="x", pady=(4, 10))
        self.input_text.insert("1.0", "汉字取模助手")

        ctk.CTkLabel(inner, text="渲染字体", text_color=C["muted"], font=ctk.CTkFont(size=12)).pack(
            anchor="w"
        )

        font_row = ctk.CTkFrame(inner, fg_color="transparent")
        font_row.pack(fill="x", pady=(4, 10))

        font_names = [os.path.basename(p) for p in list_available_fonts()]
        self.font_var = ctk.StringVar(
            value=os.path.basename(self.font_path) if self.font_path else ""
        )
        self.font_combo = ctk.CTkComboBox(
            font_row,
            values=font_names or ["(无可用字体)"],
            variable=self.font_var,
            command=self._on_font_combo,
            fg_color=C["bg"],
            border_color=C["border"],
            button_color=C["accent_dim"],
            button_hover_color=C["accent"],
            dropdown_fg_color=C["panel2"],
        )
        self.font_combo.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            font_row,
            text="浏览",
            width=56,
            fg_color=C["panel2"],
            hover_color=C["border"],
            border_width=1,
            border_color=C["border"],
            command=self._browse_font,
        ).pack(side="left", padx=(6, 0))

        self.dedupe_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            inner,
            text="自动去重",
            variable=self.dedupe_var,
            font=ctk.CTkFont(size=12),
            text_color=C["muted"],
            fg_color=C["accent"],
            hover_color=C["accent_dim"],
            border_color=C["border"],
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            inner,
            text="▶  生成字模",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=C["accent_dim"],
            hover_color=C["accent"],
            text_color=C["text"],
            command=self._on_generate,
        ).pack(fill="x")

        ctk.CTkButton(
            inner,
            text="清空",
            height=32,
            fg_color="transparent",
            hover_color=C["panel2"],
            border_width=1,
            border_color=C["border"],
            text_color=C["muted"],
            command=self._on_clear,
        ).pack(fill="x", pady=(6, 0))

    def _build_preview_panel(self, parent):
        panel = self._section(parent, "// PREVIEW")
        panel.grid(row=0, column=1, sticky="nsew", padx=6)

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.preview_scroll = ctk.CTkScrollableFrame(
            inner, fg_color=C["bg"], corner_radius=4, height=200
        )
        self.preview_scroll.pack(fill="both", expand=True, pady=(0, 10))

        detail = ctk.CTkFrame(inner, fg_color=C["bg"], corner_radius=6, border_width=1, border_color=C["border"])
        detail.pack(fill="x")

        detail_top = ctk.CTkFrame(detail, fg_color="transparent")
        detail_top.pack(fill="x", padx=12, pady=10)

        self.detail_char = ctk.CTkLabel(
            detail_top,
            text="—",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=C["text"],
        )
        self.detail_char.pack(side="left")

        self.detail_index = ctk.CTkLabel(
            detail_top,
            text="选中字符",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=C["muted"],
        )
        self.detail_index.pack(side="left", padx=12)

        preview_row = ctk.CTkFrame(detail, fg_color="transparent")
        preview_row.pack(padx=12, pady=(0, 10))

        self.large_preview = tk.Label(preview_row, bg=C["bg"])
        self.large_preview.pack(side="left")

        info = ctk.CTkFrame(preview_row, fg_color="transparent")
        info.pack(side="left", padx=16)

        self.info_utf8 = ctk.CTkLabel(
            info,
            text="UTF-8:  —",
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=C["code"],
            anchor="w",
        )
        self.info_utf8.pack(anchor="w", pady=2)

        self.info_gbk = ctk.CTkLabel(
            info,
            text="GBK:    —",
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=C["code"],
            anchor="w",
        )
        self.info_gbk.pack(anchor="w", pady=2)

        self.info_bytes = ctk.CTkLabel(
            info,
            text="点阵:   32 bytes",
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=C["muted"],
            anchor="w",
        )
        self.info_bytes.pack(anchor="w", pady=2)

    def _build_output_panel(self, parent):
        panel = self._section(parent, "// OUTPUT  (.h)")
        panel.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="复制代码",
            width=90,
            height=30,
            fg_color=C["panel2"],
            hover_color=C["border"],
            border_width=1,
            border_color=C["border"],
            command=self._on_copy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="保存 .h",
            width=90,
            height=30,
            fg_color=C["accent_dim"],
            hover_color=C["accent"],
            command=self._on_save,
        ).pack(side="left", padx=6)

        self.char_count_label = ctk.CTkLabel(
            btn_row,
            text="0 字符",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=C["muted"],
        )
        self.char_count_label.pack(side="right")

        self.output_text = ctk.CTkTextbox(
            inner,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=C["bg"],
            text_color=C["code"],
            border_color=C["border"],
            border_width=1,
            wrap="none",
        )
        self.output_text.pack(fill="both", expand=True)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["muted"],
            anchor="w",
        )
        self.status_label.pack(side="left", padx=16)

    def _set_status(self, msg: str):
        self.status_label.configure(text=msg)

    def _resolve_font_path(self) -> str:
        name = self.font_var.get()
        for path in list_available_fonts():
            if os.path.basename(path) == name:
                return path
        if os.path.isfile(self.font_path):
            return self.font_path
        raise FileNotFoundError("未找到可用中文字体")

    def _on_font_combo(self, _choice: str):
        try:
            self.font_path = self._resolve_font_path()
            self._set_status(f"字体已切换: {os.path.basename(self.font_path)}")
        except FileNotFoundError as e:
            messagebox.showerror("字体错误", str(e))

    def _browse_font(self):
        path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("字体文件", "*.ttf *.ttc *.otf"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.font_path = path
        name = os.path.basename(path)
        values = list(self.font_combo.cget("values"))
        if name not in values:
            values.append(name)
            self.font_combo.configure(values=values)
        self.font_var.set(name)
        self._set_status(f"字体已加载: {name}")

    def _on_clear(self):
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self._clear_preview()
        self.glyphs = []
        self.char_count_label.configure(text="0 字符")
        self._set_status("已清空")

    def _clear_preview(self):
        for w in self._card_widgets:
            w.destroy()
        self._card_widgets = []
        self._selected_glyph = None
        self.detail_char.configure(text="—")
        self.detail_index.configure(text="选中字符")
        self.info_utf8.configure(text="UTF-8:  —")
        self.info_gbk.configure(text="GBK:    —")
        self.large_preview.configure(image="")

    def _on_generate(self):
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "请输入汉字")
            return

        try:
            font_path = self._resolve_font_path()
        except FileNotFoundError as e:
            messagebox.showerror("字体错误", str(e))
            return

        glyphs, warnings = generate_glyphs(text, font_path, dedupe=self.dedupe_var.get())
        if not glyphs:
            messagebox.showwarning("提示", "未生成有效字模，请检查输入字符。")
            if warnings:
                messagebox.showwarning("警告", "\n".join(warnings))
            return

        self.glyphs = glyphs
        code = glyphs_to_c_code(glyphs)
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", code)
        self.char_count_label.configure(text=f"{len(glyphs)} 字符")

        self._clear_preview()
        self._rebuild_preview_cards()
        self._select_glyph(glyphs[0])

        status = f"生成完成  |  {len(glyphs)} 个汉字  |  {os.path.basename(font_path)}"
        if warnings:
            status += f"  |  {len(warnings)} 条警告"
            messagebox.showwarning("部分字符已跳过", "\n".join(warnings))
        self._set_status(status)

    def _rebuild_preview_cards(self):
        cols = 4
        for i, glyph in enumerate(self.glyphs):
            card = GlyphCard(
                self.preview_scroll,
                glyph,
                self.font_path,
                on_select=self._select_glyph,
            )
            row, col = divmod(i, cols)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="n")
            self._card_widgets.append(card)

    def _select_glyph(self, glyph: CharGlyph):
        self._selected_glyph = glyph
        for card in self._card_widgets:
            card.set_selected(card.glyph is glyph)

        self.detail_char.configure(text=glyph.char)
        self.detail_index.configure(text=f"index = {glyph.index}")

        utf8_str = " ".join(f"{b:02X}" for b in glyph.utf8)
        gbk_str = " ".join(f"{b:02X}" for b in glyph.gbk)
        self.info_utf8.configure(text=f"UTF-8:  {utf8_str}")
        self.info_gbk.configure(text=f"GBK:    {gbk_str}")

        img = bitmap_to_image(glyph.bitmap, scale=12)
        self._preview_photo = ImageTk.PhotoImage(img)
        self.large_preview.configure(image=self._preview_photo)

    def _on_copy(self):
        code = self.output_text.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("提示", "没有可复制的代码")
            return
        self.clipboard_clear()
        self.clipboard_append(code)
        self._set_status("代码已复制到剪贴板")

    def _on_save(self):
        code = self.output_text.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("提示", "没有可保存的代码")
            return
        path = filedialog.asksaveasfilename(
            title="保存字模头文件",
            defaultextension=".h",
            filetypes=[("C 头文件", "*.h"), ("所有文件", "*.*")],
            initialfile="zh16x16.h",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        self._set_status(f"已保存: {path}")
        messagebox.showinfo("保存成功", f"字模已保存至:\n{path}")


def main():
    if not list_available_fonts():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "字体缺失",
            "未找到中文字体。\n请将 simhei.ttf 放到程序目录，或安装系统字体后重试。",
        )
        sys.exit(1)

    app = OLEDStudioApp()
    app.mainloop()


if __name__ == "__main__":
    main()
