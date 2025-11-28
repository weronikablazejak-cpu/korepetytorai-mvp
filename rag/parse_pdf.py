import re
import json
from pathlib import Path
from typing import List, Dict

import pdfplumber   # <— wymaga: pip install pdfplumber


# ---------------------------------------------------------
#  📌 GŁÓWNY PARSER PDF → JSON (wersja uniwersalna)
# ---------------------------------------------------------

def extract_text_blocks(pdf_path: Path) -> List[str]:
    """Czyta PDF i zwraca listę bloków tekstu."""
    blocks = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            # Normalizacja linii
            clean = (
                text.replace("\xa0", " ")
                .replace("\t", "    ")
                .strip()
            )

            # Dodajemy stronę jako blok
            blocks.append(clean)

    return blocks


# ---------------------------------------------------------
#  📌 DETEKCJA ZADAŃ, PODZADAŃ, KRYTERIÓW
# ---------------------------------------------------------

RE_TASK = re.compile(r"^(Zadanie\s*\d+)", re.IGNORECASE)
RE_SUBTASK = re.compile(r"^([a-d]\))")
RE_POINTS = re.compile(r"(\d+)\s*pkt", re.IGNORECASE)
RE_CRITERIA = re.compile(r"^Kryteria oceniania", re.IGNORECASE)


def segment_blocks_to_items(blocks: List[str], source_pdf: str) -> List[Dict]:
    """Dzieli PDF na logiczne elementy: zadania, podzadania, teorię, kryteria."""

    items = []
    current = None
    task_number = None

    for block in blocks:
        lines = block.split("\n")

        for line in lines:
            text = line.strip()

            # --- Zadanie ---
            m = RE_TASK.match(text)
            if m:
                if current:
                    items.append(current)

                task_number = m.group(1).replace(" ", "_")

                current = {
                    "id": f"{source_pdf}__{task_number}",
                    "source_pdf": source_pdf,
                    "type": "zadanie",
                    "task_number": task_number,
                    "subtask": None,
                    "text": "",
                    "attachments": [],
                    "max_points": None,
                    "chunk_for_rag": True,
                }
                continue

            # --- Podzadanie ---
            s = RE_SUBTASK.match(text)
            if s and current:
                # dodaj poprzednie jeśli miało treść
                if current and current["text"].strip():
                    items.append(current)

                sub = s.group(1).replace(")", "")

                current = {
                    "id": f"{source_pdf}__{task_number}_{sub}",
                    "source_pdf": source_pdf,
                    "type": "zadanie",
                    "task_number": task_number,
                    "subtask": sub,
                    "text": "",
                    "attachments": [],
                    "max_points": None,
                    "chunk_for_rag": True,
                }
                continue

            # --- Kryteria ---
            k = RE_CRITERIA.match(text)
            if k:
                if current:
                    items.append(current)

                current = {
                    "id": f"{source_pdf}__{task_number}_KRYTERIA",
                    "source_pdf": source_pdf,
                    "type": "kryteria",
                    "task_number": task_number,
                    "criteria": [],
                    "max_points": None,
                    "chunk_for_rag": False,
                }
                continue

            # --- Linia z punktacją ---
            pts = RE_POINTS.search(text)
            if pts and current:
                try:
                    current["max_points"] = int(pts.group(1))
                except:
                    pass

            # --- Zwykła treść ---
            if current:
                # placeholder dla rysunku
                if "Rysunek" in text or "Schemat" in text or "Tabela" in text:
                    current["attachments"].append(f"[{text}]")
                else:
                    current["text"] += text + " "

    # dodaj ostatni element
    if current:
        items.append(current)

    return items


# ---------------------------------------------------------
#  📌 GŁÓWNA FUNKCJA: PARSE PDF → JSON FILE
# ---------------------------------------------------------

def parse_pdf_to_json(pdf_path: str, output_dir: str = "parsed"):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    blocks = extract_text_blocks(pdf_path)

    items = segment_blocks_to_items(blocks, pdf_path.name)

    output_file = output_dir / (pdf_path.stem + ".json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    return output_file, len(items)


# ---------------------------------------------------------
#  📌 TEST MANUALNY (opcjonalnie)
# ---------------------------------------------------------

if __name__ == "__main__":
    file, count = parse_pdf_to_json("MCHP-R0-100-A-2505-arkusz.pdf")
    print(f"Wygenerowano {count} elementów → {file}")
