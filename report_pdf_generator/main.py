#!/usr/bin/env python3
"""
Assignment Report Generator — Polished Dark GUI
Install: pip install reportlab Pillow
(tkinter ships with Python)
"""

import os
import json
import re
import sys
from pathlib import Path
from itertools import groupby
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from PIL import Image as PILImage

# ── Constants ─────────────────────────────────────────────────────────────────
BASE_DIR         = Path.home() / "Documents" / "ReportGenerator"
USER_INFO_FILE   = str(BASE_DIR / "user_info.json")
REPORTS_BASE_DIR = BASE_DIR / "Reports"

PAGE_W, PAGE_H = A4
MARGIN = 50.0
FOOTER_HEIGHT = 30.0
HEADER_HEIGHT = 60.0

# Palette — refined dark theme
BG           = "#1a1a2e"
SURFACE      = "#16213e"
SURFACE2     = "#0f3460"
BORDER       = "#1f4e8c"
ACCENT       = "#4cc9f0"
ACCENT2      = "#7209b7"
SUCCESS      = "#06d6a0"
ERROR        = "#ef233c"
FG           = "#e2e8f0"
FG_DIM       = "#94a3b8"
INPUT_BG     = "#0d1b2a"
BUTTON_HVR   = "#5dddf7"

FONT_NORMAL     = ("Courier", 11)
FONT_BOLD       = ("Courier", 11, "bold")
FONT_SMALL      = ("Courier", 10)
FONT_ITALIC     = ("Courier", 10, "italic")
FONT_HEADER     = ("Courier", 22, "bold")
FONT_ACCENT_LBL = ("Courier", 11, "bold")


# ══════════════════════════════════════════════════════════════════════════════
# Startup — ensure folders exist
# ══════════════════════════════════════════════════════════════════════════════

def ensure_dirs():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_BASE_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# Data Management
# ══════════════════════════════════════════════════════════════════════════════

def load_user_info():
    if os.path.exists(USER_INFO_FILE):
        with open(USER_INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "", "id": "", "submitted_assignments": {}, "saved_groups": {}}

def save_user_info(info):
    with open(USER_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4, ensure_ascii=False)

def update_submitted_assignments(course, assignment, user_info):
    submitted = user_info.setdefault("submitted_assignments", {})
    course_list = submitted.setdefault(course, [])
    if assignment not in course_list:
        course_list.append(assignment)
    save_user_info(user_info)


# ══════════════════════════════════════════════════════════════════════════════
# Image Helpers
# ══════════════════════════════════════════════════════════════════════════════

def read_images(folder):
    folder = Path(folder)
    image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}
    if not folder.is_dir():
        return []
    files = [f for f in folder.iterdir()
             if f.suffix.lower() in image_exts and not f.name.startswith(".")]

    def sort_key(fp):
        m = re.search(r"Q(\d+)_(\d+)", fp.stem, re.IGNORECASE)
        return (int(m.group(1)), int(m.group(2))) if m else (float("inf"), fp.stem)

    files.sort(key=sort_key)
    return [str(f) for f in files]

def get_scaled_size(img_path, available_w, available_h):
    with PILImage.open(img_path) as img:
        img_w, img_h = img.size
    scale = min(available_w / img_w, available_h / img_h)
    return img_w * scale, img_h * scale

def group_images_by_question(images):
    def q_num(path):
        m = re.search(r"Q(\d+)", Path(path).stem, re.IGNORECASE)
        return int(m.group(1)) if m else None
    groups = []
    for q, imgs in groupby(images, key=q_num):
        groups.append((q, list(imgs)))
    return groups

def build_page_groups(images, content_h):
    available_w = PAGE_W - 2 * MARGIN
    pages = []
    for _q, imgs in group_images_by_question(images):
        i = 0
        while i < len(imgs):
            if i + 1 < len(imgs):
                half_h = (content_h - MARGIN) / 2
                try:
                    _, h1 = get_scaled_size(imgs[i],     available_w, half_h)
                    _, h2 = get_scaled_size(imgs[i + 1], available_w, half_h)
                    if h1 + h2 + MARGIN <= content_h:
                        pages.append([imgs[i], imgs[i + 1]])
                        i += 2
                        continue
                except Exception:
                    pass
            pages.append([imgs[i]])
            i += 1
    return pages


# ══════════════════════════════════════════════════════════════════════════════
# PDF Generation
# ══════════════════════════════════════════════════════════════════════════════

def create_pdf(images, course, assignment, mode, user_info, group_members=None):
    course_folder = REPORTS_BASE_DIR / course
    course_folder.mkdir(parents=True, exist_ok=True)
    pdf_path = str(course_folder / f"{assignment}.pdf")
    c = rl_canvas.Canvas(pdf_path, pagesize=A4)

    if mode == "group":
        content_h = PAGE_H - 2 * MARGIN - FOOTER_HEIGHT
        pages = build_page_groups(images, content_h)
        total_pages = len(pages) + 1
        _draw_group_cover(c, group_members, course, assignment)
        c.showPage()
        available_w = PAGE_W - 2 * MARGIN
        for page_idx, img_group in enumerate(pages, start=2):
            if len(img_group) == 2:
                _draw_two_images(c, img_group[0], img_group[1], available_w, content_h)
            else:
                _draw_one_image(c, img_group[0], available_w, content_h, top_y=PAGE_H - MARGIN)
            _draw_footer(c, page_idx, total_pages)
            c.showPage()
    else:
        content_h_p1   = PAGE_H - MARGIN - HEADER_HEIGHT - FOOTER_HEIGHT - MARGIN
        content_h_rest = PAGE_H - 2 * MARGIN - FOOTER_HEIGHT
        pages = build_page_groups(images, content_h_p1)
        total_pages = len(pages)
        available_w = PAGE_W - 2 * MARGIN

        for page_idx, img_group in enumerate(pages, start=1):
            is_first = (page_idx == 1)
            if is_first:
                _draw_individual_header(c, user_info, course, assignment)
                top_y     = PAGE_H - MARGIN - HEADER_HEIGHT
                content_h = content_h_p1
            else:
                top_y     = PAGE_H - MARGIN
                content_h = content_h_rest

            if len(img_group) == 2:
                _draw_two_images(c, img_group[0], img_group[1], available_w, content_h, top_y=top_y)
            else:
                _draw_one_image(c, img_group[0], available_w, content_h, top_y=top_y)
            _draw_footer(c, page_idx, total_pages)
            c.showPage()

    c.save()
    return pdf_path

def _draw_group_cover(c, members, course, assignment):
    cx = PAGE_W / 2
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.black)
    c.drawCentredString(cx, PAGE_H - MARGIN - 50, course)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(cx, PAGE_H - MARGIN - 90, assignment)
    rule_y = PAGE_H - MARGIN - 118
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.line(MARGIN * 2, rule_y, PAGE_W - MARGIN * 2, rule_y)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(cx, rule_y - 28, "Group Members")
    y = rule_y - 55
    for i, member in enumerate(members, start=1):
        if y < MARGIN + 40:
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(cx, y, f"... and {len(members) - i + 1} more member(s)")
            break
        c.setFont("Helvetica-Bold", 13)
        c.drawString(MARGIN + 20, y, f"{i}.  {member['name']}")
        c.setFont("Helvetica", 12)
        c.drawString(MARGIN + 30, y - 18, f"ID: {member['id']}")
        y -= 48

def _draw_individual_header(c, user_info, course, assignment):
    top_y = PAGE_H - MARGIN
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.black)
    c.drawString(MARGIN, top_y,      f"Course: {course}    Assignment: {assignment}")
    c.drawString(MARGIN, top_y - 22, f"Name: {user_info['name']}    ID: {user_info['id']}")
    rule_y = top_y - 40
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(MARGIN, rule_y, PAGE_W - MARGIN, rule_y)

def _draw_one_image(c, img_path, available_w, available_h, top_y):
    try:
        draw_w, draw_h = get_scaled_size(img_path, available_w, available_h)
    except Exception as e:
        print(f"Warning: Could not open {img_path} - {e}")
        return
    image_x = (PAGE_W - draw_w) / 2
    image_y = top_y - draw_h
    _draw_question_label(c, img_path, image_y + draw_h + 4)
    c.drawImage(img_path, image_x, image_y, width=draw_w, height=draw_h,
                preserveAspectRatio=True, mask="auto")

def _draw_two_images(c, img_path1, img_path2, available_w, available_h, top_y=None):
    if top_y is None:
        top_y = PAGE_H - MARGIN
    gap = MARGIN
    half_h = (available_h - gap) / 2
    for slot, img_path in enumerate([img_path1, img_path2]):
        try:
            draw_w, draw_h = get_scaled_size(img_path, available_w, half_h)
        except Exception as e:
            print(f"Warning: Could not open {img_path} - {e}")
            continue
        image_x = (PAGE_W - draw_w) / 2
        if slot == 0:
            image_y = top_y - draw_h
        else:
            _, h1 = get_scaled_size(img_path1, available_w, half_h)
            image_y = top_y - h1 - gap - draw_h
        _draw_question_label(c, img_path, image_y + draw_h + 4)
        c.drawImage(img_path, image_x, image_y, width=draw_w, height=draw_h,
                    preserveAspectRatio=True, mask="auto")

def _draw_question_label(c, img_path, label_y):
    m = re.search(r"Q(\d+)", Path(img_path).stem, re.IGNORECASE)
    if m:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(MARGIN, label_y, f"Question {m.group(1)}")

def _draw_footer(c, page_num, total_pages):
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_W / 2.0, MARGIN - 10, f"Page {page_num} of {total_pages}")


# ══════════════════════════════════════════════════════════════════════════════
# Reusable UI Helpers
# ══════════════════════════════════════════════════════════════════════════════

def make_card(parent, title="", **kwargs):
    outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=SURFACE, padx=18, pady=14)
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title, bg=SURFACE, fg=ACCENT,
                 font=FONT_ACCENT_LBL).pack(anchor="w", pady=(0, 8))
    return outer, inner

def make_label(parent, text, dim=False, **kwargs):
    return tk.Label(parent, text=text, bg=SURFACE,
                    fg=FG_DIM if dim else FG,
                    font=FONT_NORMAL, **kwargs)

def make_entry(parent, textvariable, width=38, **kwargs):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=INPUT_BG, fg=FG, insertbackground=ACCENT,
                    relief="flat", bd=0,
                    highlightthickness=1, highlightcolor=ACCENT,
                    highlightbackground=BORDER,
                    font=FONT_NORMAL, **kwargs)

def make_button(parent, text, command, accent=False, danger=False, **kwargs):
    bg  = ACCENT if accent  else (ERROR if danger else SURFACE2)
    fg  = BG     if accent  else FG
    hbg = BUTTON_HVR if accent else BORDER
    return tk.Button(parent, text=text, command=command,
                     bg=bg, fg=fg, activebackground=hbg, activeforeground=fg,
                     relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                     font=FONT_BOLD, **kwargs)

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)


# ══════════════════════════════════════════════════════════════════════════════
# Simple input dialog
# ══════════════════════════════════════════════════════════════════════════════

class _InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text=prompt, bg=SURFACE, fg=FG, font=FONT_NORMAL,
                 justify="left").pack(padx=20, pady=(16, 8))

        self._var = tk.StringVar()
        e = make_entry(self, self._var, width=30)
        e.pack(padx=20, pady=(0, 12))
        e.focus_set()

        btn_row = tk.Frame(self, bg=SURFACE)
        btn_row.pack(pady=(0, 16))
        make_button(btn_row, "OK",     command=self._ok,     accent=True).pack(side="left", padx=6)
        make_button(btn_row, "Cancel", command=self.destroy).pack(side="left", padx=6)

        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())

        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w)//2}+{py + (ph - h)//2}")
        self.wait_window()

    def _ok(self):
        self.result = self._var.get().strip() or None
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Main Application
# ══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Assignment Report Generator")
        self.root.configure(bg=BG)
        self.root.geometry("720x860")
        self.root.resizable(True, True)
        self.root.minsize(620, 660)

        self.user_info = load_user_info()
        self.user_info.setdefault("saved_groups", {})
        self.mode = tk.StringVar(value="individual")

        self._build_ui()
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview, bg=SURFACE)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(canvas, bg=BG)
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        content = self.scroll_frame
        pad = dict(padx=24, pady=8)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(content, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))

        tk.Label(hdr, text="◈  Assignment Report Generator",
                 bg=BG, fg=ACCENT, font=FONT_HEADER).pack(side="left")
        tk.Label(hdr, text="PDF builder",
                 bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left", padx=(10, 0), pady=(8, 0))

        tk.Frame(content, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(4, 12))

        self._build_user_card(content, **pad)
        self._build_mode_card(content, **pad)

        self.group_outer, self.group_inner = make_card(content, title="◈ Group Members")
        self._build_group_inner()

        self._build_assignment_card(content, **pad)
        self._build_log_card(content, **pad)
        self._build_actions(content, **pad)

    # ── User info ─────────────────────────────────────────────────────────────

    def _build_user_card(self, parent, **kw):
        outer, card = make_card(parent, title="◈ Your Information")
        outer.pack(fill="x", **kw)

        self.name_var = tk.StringVar(value=self.user_info.get("name", ""))
        self.id_var   = tk.StringVar(value=self.user_info.get("id", ""))

        self._field_row(card, "Full Name", self.name_var)
        self._field_row(card, "Student ID", self.id_var)

    # ── Mode ──────────────────────────────────────────────────────────────────

    def _build_mode_card(self, parent, **kw):
        outer, card = make_card(parent, title="◈ Submission Mode")
        outer.pack(fill="x", **kw)
        self.mode_outer = outer

        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x")

        for label, val in [("  Individual", "individual"), ("  Group", "group")]:
            rb = tk.Radiobutton(row, text=label, variable=self.mode, value=val,
                                bg=SURFACE, fg=FG, selectcolor=INPUT_BG,
                                activebackground=SURFACE, activeforeground=ACCENT,
                                font=FONT_NORMAL, indicatoron=False,
                                relief="flat", bd=0,
                                highlightthickness=1, highlightbackground=BORDER,
                                padx=20, pady=8, cursor="hand2",
                                command=self._on_mode_change)
            rb.pack(side="left", padx=(0, 8))

    # ── Group members ─────────────────────────────────────────────────────────

    def _build_group_inner(self):
        card = self.group_inner

        save_row = tk.Frame(card, bg=SURFACE)
        save_row.pack(fill="x", pady=(0, 6))

        tk.Label(save_row, text="Group Name:", bg=SURFACE, fg=FG_DIM,
                 font=FONT_SMALL).pack(side="left")

        self.group_name_var = tk.StringVar()
        make_entry(save_row, self.group_name_var, width=20).pack(side="left", padx=6)

        make_button(save_row, "💾  Save Group",
                    command=self._save_group).pack(side="left", padx=(0, 6))

        self.saved_group_var = tk.StringVar(value="Load saved…")
        self.saved_group_menu = tk.OptionMenu(
            save_row, self.saved_group_var, "Load saved…",
            command=self._load_saved_group)
        self.saved_group_menu.config(
            bg=SURFACE2, fg=FG, activebackground=BORDER, activeforeground=ACCENT,
            font=FONT_SMALL, relief="flat", bd=0, highlightthickness=0, cursor="hand2")
        self.saved_group_menu["menu"].config(
            bg=SURFACE2, fg=FG, activebackground=BORDER, font=FONT_SMALL)
        self.saved_group_menu.pack(side="left", padx=(4, 0))

        self._refresh_saved_group_menu()

        divider(card)

        top = tk.Frame(card, bg=SURFACE)
        top.pack(fill="x", pady=(0, 10))

        make_label(top, "Number of members:").pack(side="left")

        self.num_participants = tk.StringVar(value="2")
        tk.Spinbox(top, from_=1, to=20,
                   textvariable=self.num_participants,
                   bg=INPUT_BG, fg=FG, buttonbackground=SURFACE2,
                   relief="flat", bd=0,
                   highlightthickness=1, highlightcolor=ACCENT,
                   highlightbackground=BORDER,
                   font=FONT_NORMAL,
                   width=4, justify="center").pack(side="left", padx=8)

        make_button(top, "Generate Fields",
                    command=self._generate_member_fields).pack(side="left", padx=6)

        divider(card)

        header = tk.Frame(card, bg=SURFACE)
        header.pack(fill="x")
        make_label(header, "Name", dim=True).pack(side="left", expand=True, anchor="w")
        make_label(header, "Student ID", dim=True).pack(side="left", padx=24, anchor="w")

        self.members_container = tk.Frame(card, bg=SURFACE)
        self.members_container.pack(fill="x")
        self.member_vars: list[tuple[tk.StringVar, tk.StringVar]] = []

    def _generate_member_fields(self, members=None):
        for w in self.members_container.winfo_children():
            w.destroy()
        self.member_vars.clear()

        try:
            num = int(self.num_participants.get())
            if num < 1:
                raise ValueError
        except ValueError:
            self._log("⚠ Please enter a valid number of members")
            return

        pre = members or []

        for i in range(1, num + 1):
            is_you = (i == 1)
            row = tk.Frame(self.members_container, bg=SURFACE)
            row.pack(fill="x", pady=4)

            tk.Label(row, text=f"{i:>2}.",
                     bg=SURFACE2 if is_you else SURFACE,
                     fg=ACCENT if is_you else FG_DIM,
                     font=FONT_BOLD,
                     width=3, padx=4, pady=4).pack(side="left", padx=(0, 6))

            if pre and i - 1 < len(pre):
                default_name = pre[i - 1].get("name", "")
                default_id   = pre[i - 1].get("id", "")
            else:
                default_name = self.name_var.get() if is_you else ""
                default_id   = self.id_var.get()   if is_you else ""

            n_var = tk.StringVar(value=default_name)
            i_var = tk.StringVar(value=default_id)
            self.member_vars.append((n_var, i_var))

            make_entry(row, n_var, width=26).pack(side="left", padx=(0, 8))
            make_entry(row, i_var, width=16).pack(side="left")

            if is_you:
                tk.Label(row, text=" ← you", bg=SURFACE, fg=ACCENT2,
                         font=FONT_ITALIC).pack(side="left", padx=4)

        self._log(f"✔ Generated {num} member field(s)")

    # ── Save / load group ─────────────────────────────────────────────────────

    def _save_group(self):
        name = self.group_name_var.get().strip()
        if not name:
            ans = messagebox.askyesno(
                "Name Your Group?",
                "Would you like to give this group a name?\n\n"
                "Saving with a name means next time you only pick the group\n"
                "from the dropdown — no re-typing names or IDs!\n\n"
                "Click Yes to enter a name, No to cancel."
            )
            if not ans:
                return
            dlg = _InputDialog(self.root, "Group Name",
                                'Enter a group name  (e.g. "Group 5" or "Team Alpha"):')
            name = dlg.result
            if not name:
                return
            self.group_name_var.set(name)

        if not self.member_vars:
            messagebox.showwarning("No Members",
                "Click 'Generate Fields' and fill in member info first.")
            return

        members = [
            {"name": n.get().strip(), "id": i.get().strip()}
            for n, i in self.member_vars
            if n.get().strip() or i.get().strip()
        ]
        if not members:
            messagebox.showwarning("Empty Fields",
                "Please fill in at least one member before saving.")
            return

        self.user_info.setdefault("saved_groups", {})[name] = members
        save_user_info(self.user_info)
        self._refresh_saved_group_menu()
        self._log(f'✔ Group "{name}" saved ({len(members)} member(s))', "success")

    def _load_saved_group(self, name):
        if name == "Load saved…":
            return
        groups = self.user_info.get("saved_groups", {})
        if name not in groups:
            return
        members = groups[name]
        self.group_name_var.set(name)
        self.num_participants.set(str(len(members)))
        self._generate_member_fields(members=members)
        self._log(f'✔ Loaded group "{name}" — {len(members)} member(s)', "success")

    def _refresh_saved_group_menu(self):
        menu = self.saved_group_menu["menu"]
        menu.delete(0, "end")
        menu.add_command(label="Load saved…",
                         command=lambda: self.saved_group_var.set("Load saved…"))
        for gname in self.user_info.get("saved_groups", {}):
            menu.add_command(label=gname,
                             command=lambda g=gname: self._load_saved_group(g))

    # ── Assignment details ────────────────────────────────────────────────────

    def _build_assignment_card(self, parent, **kw):
        outer, card = make_card(parent, title="◈ Assignment Details")
        outer.pack(fill="x", **kw)

        self.course_var = tk.StringVar()
        self.assign_var = tk.StringVar()
        self.folder_var = tk.StringVar()

        self._field_row(card, "Course", self.course_var)
        self._field_row(card, "Assignment", self.assign_var)

        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x", pady=4)
        make_label(row, f"{'Screenshots':<13}").pack(side="left")
        make_entry(row, self.folder_var, width=26).pack(side="left", expand=True, fill="x")
        make_button(row, "Browse", command=self._browse_folder).pack(side="left", padx=(8, 0))

    # ── Log ───────────────────────────────────────────────────────────────────

    def _build_log_card(self, parent, **kw):
        outer, card = make_card(parent, title="◈ Status Log")
        outer.pack(fill="x", **kw)

        self.log_box = tk.Text(card, height=7,
                               bg=INPUT_BG, fg=SUCCESS,
                               insertbackground=ACCENT,
                               relief="flat", bd=0,
                               font=FONT_SMALL,
                               state="disabled",
                               highlightthickness=1,
                               highlightbackground=BORDER)
        self.log_box.pack(fill="both", expand=True)

        self.log_box.tag_config("info",    foreground=FG_DIM)
        self.log_box.tag_config("success", foreground=SUCCESS)
        self.log_box.tag_config("warn",    foreground="#ffd166")
        self.log_box.tag_config("error",   foreground=ERROR)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _build_actions(self, parent, **kw):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", **kw)

        make_button(row, "⚙  Generate PDF", command=self._generate,
                    accent=True).pack(side="left", expand=True, fill="x", padx=(0, 6))
        make_button(row, "✕  Quit", command=self.root.quit,
                    danger=True).pack(side="left", padx=(6, 0))

        tk.Frame(parent, bg=BG, height=16).pack()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _field_row(self, card, label, var):
        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x", pady=4)
        make_label(row, f"{label:<13}").pack(side="left")
        make_entry(row, var).pack(side="left", expand=True, fill="x")

    def _on_mode_change(self):
        if self.mode.get() == "group":
            self.group_outer.pack(fill="x", padx=24, pady=8, after=self.mode_outer)
        else:
            self.group_outer.pack_forget()

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_var.set(folder)
        images = read_images(folder)
        if images:
            questions = sorted({
                m.group(1)
                for path in images
                if (m := re.search(r"Q(\d+)", Path(path).stem, re.IGNORECASE))
            })
            self._log(f"✔ {len(images)} image(s) found — questions: {', '.join(questions) or 'auto'}", "success")
        else:
            self._log("⚠ No supported images found in that folder", "warn")

    def _log(self, msg: str, tag: str = "info"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"  {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.root.update_idletasks()

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── Generate ──────────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        checks = [
            (self.name_var,   "your full name"),
            (self.id_var,     "your student ID"),
            (self.course_var, "the course name"),
            (self.assign_var, "the assignment name"),
            (self.folder_var, "a screenshots folder"),
        ]
        for var, label in checks:
            if not var.get().strip():
                messagebox.showerror("Missing Field", f"Please fill in {label}.")
                return False

        if self.mode.get() == "group":
            if not hasattr(self, "member_vars") or not self.member_vars:
                messagebox.showerror("Group Members",
                    "Please click 'Generate Fields' and fill in your group members.")
                return False
            valid = [(n.get().strip(), i.get().strip())
                     for n, i in self.member_vars if n.get().strip() and i.get().strip()]
            if not valid:
                messagebox.showerror("Group Members",
                    "Please fill in at least one group member's name and ID.")
                return False

        return True

    def _generate(self):
        if not self._validate():
            return

        self.user_info["name"] = self.name_var.get().strip()
        self.user_info["id"]   = self.id_var.get().strip()
        save_user_info(self.user_info)

        images = read_images(self.folder_var.get())
        if not images:
            messagebox.showerror("No Images",
                "No supported images were found in the selected folder.")
            return

        group_members = None
        if self.mode.get() == "group":
            group_members = [
                {"name": n.get().strip(), "id": i.get().strip()}
                for n, i in self.member_vars
                if n.get().strip() and i.get().strip()
            ]

            current_name  = self.group_name_var.get().strip()
            saved_groups  = self.user_info.get("saved_groups", {})
            if not current_name or current_name not in saved_groups:
                ans = messagebox.askyesno(
                    "Save This Group?",
                    "Would you like to save this group for future assignments?\n\n"
                    "Next time, just pick the group from the dropdown and\n"
                    "everyone's name & ID will fill in automatically!"
                )
                if ans:
                    dlg = _InputDialog(self.root, "Group Name",
                                       'Enter a name for this group\n(e.g. "Group 5" or "Team Alpha"):')
                    gname = dlg.result
                    if gname:
                        self.group_name_var.set(gname)
                        self.user_info.setdefault("saved_groups", {})[gname] = group_members
                        save_user_info(self.user_info)
                        self._refresh_saved_group_menu()
                        self._log(f'✔ Group "{gname}" saved for future use', "success")

        self._log(f"Building PDF — {len(images)} image(s)...")

        try:
            pdf_path = create_pdf(
                images,
                self.course_var.get().strip(),
                self.assign_var.get().strip(),
                self.mode.get(),
                self.user_info,
                group_members,
            )
            update_submitted_assignments(
                self.course_var.get().strip(),
                self.assign_var.get().strip(),
                self.user_info,
            )
            self._log(f"✔ PDF saved → {pdf_path}", "success")

            if messagebox.askyesno("Done!", f"PDF created:\n{pdf_path}\n\nOpen folder?"):
                if sys.platform == "win32":
                    os.startfile(os.path.dirname(pdf_path))
                elif sys.platform == "darwin":
                    os.system(f'open "{os.path.dirname(pdf_path)}"')
                else:
                    os.system(f'xdg-open "{os.path.dirname(pdf_path)}"')

        except Exception as exc:
            self._log(f"✘ {exc}", "error")
            messagebox.showerror("Error", f"PDF generation failed:\n{exc}")


# ══════════════════════════════════════════════════════════════════════════════

def main():
    ensure_dirs()
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()