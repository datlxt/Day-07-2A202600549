"""Group dataset loader — Vietnamese film screenplays.

Shared by all team members so everyone benchmarks on the SAME documents and
the SAME agreed metadata schema:
    doc_id, title, genre, year, director
"""
from __future__ import annotations

from pathlib import Path

from src.models import Document

DATA_DIR = Path(__file__).parent / "data"

# Per-film metadata. `genre` uses a single primary label so exact-match
# metadata filtering works (e.g. filter genre="hoc_duong" -> student films).
FILMS: dict[str, dict] = {
    "bui_doi_cho_lon": {
        "title": "BỤI ĐỜI CHỢ LỚN",
        "genre": "hanh_dong",
        "year": 2013,
        "director": "Charlie Nguyễn",
    },
    "co_gai_den_tu_hom_qua": {
        "title": "CÔ GÁI ĐẾN TỪ HÔM QUA",
        "genre": "hoc_duong",
        "year": 2017,
        "director": "Phan Gia Nhật Linh",
    },
    "nguoi_bat_tu": {
        "title": "NGƯỜI BẤT TỬ",
        "genre": "ky_ao",
        "year": 2018,
        "director": "Victor Vũ",
    },
    "nham_mat_thay_mua_he": {
        "title": "NHẮM MẮT THẤY MÙA HÈ",
        "genre": "lang_man",
        "year": 2018,
        "director": "Cao Thúy Nhi",
    },
    "thang_nam_ruc_ro": {
        "title": "THÁNG NĂM RỰC RỠ",
        "genre": "hoc_duong",
        "year": 2018,
        "director": "Nguyễn Quang Dũng",
    },
    "toi_thay_hoa_vang_tren_co_xanh": {
        "title": "TÔI THẤY HOA VÀNG TRÊN CỎ XANH",
        "genre": "tam_ly",
        "year": 2015,
        "director": "Victor Vũ",
    },
}


def load_group_documents() -> list[Document]:
    """Read each film screenplay from data/ and attach the group metadata."""
    documents: list[Document] = []
    for doc_id, info in FILMS.items():
        path = DATA_DIR / f"{doc_id}.md"
        content = path.read_text(encoding="utf-8")
        metadata = {
            "doc_id": doc_id,
            "title": info["title"],
            "genre": info["genre"],
            "year": info["year"],
            "director": info["director"],
        }
        documents.append(Document(id=doc_id, content=content, metadata=metadata))
    return documents


if __name__ == "__main__":
    for doc in load_group_documents():
        print(f"{doc.id:35s} {len(doc.content):>7d} chars  meta={doc.metadata}")
