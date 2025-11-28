from pathlib import Path
from rag.parse_pdf import parse_pdf_to_json

# katalog z PDF-ami (arkusze, kryteria, teoria)
BASE_DIR = Path(__file__).resolve().parent
MATERIALS_DIR = BASE_DIR / "app" / "materials"

# katalog na wynikowe JSON-y
OUTPUT_DIR = BASE_DIR / "rag" / "parsed"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_files = list(MATERIALS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[PDF] Brak plików PDF w {MATERIALS_DIR}")
        return

    print(f"[PDF] Znaleziono {len(pdf_files)} plików PDF.")
    for pdf in pdf_files:
        print(f"[PDF] Przetwarzam: {pdf.name}")
        out_file, count = parse_pdf_to_json(str(pdf), output_dir=str(OUTPUT_DIR))
        print(f"   → {count} elementów → {out_file.name}")

    print("[PDF] Gotowe.")


if __name__ == "__main__":
    main()
