# Report PDF Generator

**A deterministic, local-first PDF generation system for structured academic submissions.**

This project is a constraint-based rendering engine designed to transform raw screenshots and metadata into professional, submission-ready PDFs. It prioritizes **layout computation**, **state persistence**, and **reproducibility** over superficial UI.

---

## 🎯 Core Philosophy
The goal was to design a small-scale system that mirrors quantitative and systems-level problem-solving:
1. **Define constraints** (Page boundaries, image ratios, margins).
2. **Model the transformation** (Input folder → Structured PDF).
3. **Control the output surface** (Pixel-perfect coordinate rendering).

> **Note:** This system is built for zero network dependency. Everything runs locally; your data never leaves your machine.

---

## 🏗️ Architecture Overview



### 1. Input Layer
* **User Metadata:** Persistent JSON store for student credentials and course details.
* **Ingestion Pipeline:** Automatic monitoring of screenshot directories.
* **Structured Parsing:** Regex-based identification of question numbers and sub-indices from filenames (e.g., `Q1_a.png`).

### 2. Processing Layer
* **Iterator Grouping:** Logical grouping of images by question ID using stable sorting.
* **Constraint Engine:** Pagination is computed, not guessed. 
    * *Layout Feasibility:* Two-image placement occurs only if height constraints pass.
    * *Predictable Degradation:* Automatically falls back to single-image layout if constraints are violated.
* **Dynamic Scaling:** Real-time calculation of bounding-box constraints to maintain aspect ratios.

### 3. Rendering Layer
* **Direct Canvas Rendering:** Powered by `reportlab` for explicit coordinate-based drawing.
* **Manual Control:** Custom header/footer injection without the overhead of template engines.
* **Determinism:** The same input state will *always* produce the exact same PDF byte-stream.

---

## 🛠️ Technology Stack

| Category | Tools / Concepts |
| :--- | :--- |
| **Core Logic** | Python 3, Constraint-based layout engine, Deterministic pagination |
| **State Management** | Persistent JSON storage, Versionable state, Structured file system |
| **Data Processing** | Regex (Structured parsing), Iterator grouping |
| **Rendering/GUI** | `reportlab` (PDF engine), `Pillow` (Image scaling), `tkinter` (GUI shell) |

---

## 📑 Design Principles

* **Local-First Execution:** No external APIs, telemetry, or cloud dependencies.
* **Deterministic Output:** Elimination of "hidden side effects" in the rendering pipeline.
* **Constraint-Aware:** Layout adapts dynamically based on image geometry.
* **Minimal Dependencies:** Built with a lean stack to ensure long-term reproducibility.

---

## 🚀 Usage

1. **Configure:** Update `metadata.json` with your student information.
2. **Stage:** Place your screenshots in the `/input` folder following the `Q{n}_{sub}.png` naming convention.
3. **Execute:** Run the generator to compute the layout and render the PDF.

---

## bash
python main.py

---

## This project is small in scope, but intentionally structured like a system rather than a script.
