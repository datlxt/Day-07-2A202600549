"""Group benchmark runner — Vietnamese film screenplays (mock embeddings).

CÁCH DÙNG (mỗi thành viên):
    1. Đổi MY_NAME và STRATEGY bên dưới sang chunker + tham số của BẠN.
    2. Chạy:  python benchmark_me.py
    3. Chép phần "KET QUA TONG" + bảng top-3 vào REPORT.md (Section 3 & 6).

Mọi người dùng CHUNG: bộ tài liệu (group_data) + 5 queries + gold answers.
Chỉ STRATEGY là khác nhau giữa các thành viên -> để so sánh.
"""
from __future__ import annotations

from group_data import load_group_documents
from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    RecursiveChunker,  # noqa: F401  (để thành viên đổi STRATEGY)
    SentenceChunker,  # noqa: F401  (để thành viên đổi STRATEGY)
    _mock_embed,
)

# ====================== CHỈNH 2 DÒNG NÀY ======================
MY_NAME = "Đạt"
STRATEGY = FixedSizeChunker(chunk_size=500, overlap=50)
# Ví dụ các bạn khác:
#   STRATEGY = SentenceChunker(max_sentences_per_chunk=4)
#   STRATEGY = RecursiveChunker(chunk_size=500)
# =============================================================

# query, expected doc_id(s) chứa câu trả lời, optional metadata_filter
QUERIES = [
    ("Nhân vật chính trong Tôi Thấy Hoa Vàng Trên Cỏ Xanh là ai?",
     {"toi_thay_hoa_vang_tren_co_xanh"}, None),
    ("Chủ đề phim Bụi Đời Chợ Lớn là gì?",
     {"bui_doi_cho_lon"}, None),
    ("Bối cảnh tình yêu trong Nhắm Mắt Thấy Mùa Hè diễn ra ở đâu?",
     {"nham_mat_thay_mua_he"}, None),
    ("Khả năng đặc biệt trong Người Bất Tử là gì?",
     {"nguoi_bat_tu"}, None),
    ("Phim nào có bối cảnh học sinh?",
     {"co_gai_den_tu_hom_qua", "thang_nam_ruc_ro"}, {"genre": "hoc_duong"}),
]


def build_store(films: list[Document]) -> EmbeddingStore:
    """Chunk every film with the chosen STRATEGY, then store each chunk."""
    store = EmbeddingStore(collection_name="bench", embedding_fn=_mock_embed)
    for film in films:
        for i, piece in enumerate(STRATEGY.chunk(film.content)):
            meta = dict(film.metadata)
            meta["chunk_index"] = i
            store.add_documents([Document(id=f"{film.id}__c{i}", content=piece, metadata=meta)])
    return store


def score_query(results: list[dict], expected: set[str]) -> int:
    """2 = đúng phim ở rank 1, 1 = đúng phim ở rank 2-3, 0 = không có."""
    hit_ranks = [i for i, r in enumerate(results) if r["metadata"]["doc_id"] in expected]
    if not hit_ranks:
        return 0
    return 2 if hit_ranks[0] == 0 else 1


def print_baseline(films: list[Document]) -> None:
    print("=" * 72)
    print("BASELINE — ChunkingStrategyComparator (chunk_size=200) trên 2 phim")
    print("=" * 72)
    comparator = ChunkingStrategyComparator()
    for film in films[:2]:
        print(f"\n[{film.metadata['title']}]")
        for name, stats in comparator.compare(film.content, chunk_size=200).items():
            print(f"  {name:13s} count={stats['count']:4d}  avg_length={stats['avg_length']:.1f}")


def main() -> None:
    films = load_group_documents()
    print_baseline(films)

    store = build_store(films)
    print("\n" + "=" * 72)
    print(f"RETRIEVAL — {MY_NAME} | strategy = {STRATEGY.__class__.__name__}")
    print(f"Tổng số chunk: {store.get_collection_size()}")
    print("=" * 72)

    total = 0
    for n, (query, expected, mfilter) in enumerate(QUERIES, start=1):
        if mfilter:
            results = store.search_with_filter(query, top_k=3, metadata_filter=mfilter)
        else:
            results = store.search(query, top_k=3)
        pts = score_query(results, expected)
        total += pts
        print(f"\nQ{n} ({pts}/2): {query}" + (f"   [filter={mfilter}]" if mfilter else ""))
        for rank, r in enumerate(results, start=1):
            mark = "✓" if r["metadata"]["doc_id"] in expected else " "
            preview = r["content"][:70].replace("\n", " ")
            print(f"  {mark} {rank}. score={r['score']:.3f} [{r['metadata']['title']}] {preview}...")

    print("\n" + "=" * 72)
    print(f"KET QUA TONG — {MY_NAME}: {total}/10  (Retrieval Quality)")
    print("=" * 72)


if __name__ == "__main__":
    main()
