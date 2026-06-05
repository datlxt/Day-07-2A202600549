# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lê Xuân Tiến Đạt
**Nhóm:** 16383
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn text có vector embedding chỉ về cùng một hướng trong không gian nhiều chiều, nghĩa là chúng có nội dung/ngữ nghĩa gần giống nhau (cùng chủ đề, cùng ý).

**Ví dụ HIGH similarity:**
- Sentence A: "Con chó đang chạy trong sân."
- Sentence B: "Một chú chó chạy ngoài vườn."
- Tại sao tương đồng: Cùng nói về một con chó đang chạy; chỉ khác vài từ, ý nghĩa gần như trùng.

**Ví dụ LOW similarity:**
- Sentence A: "Hôm nay trời mưa rất to."
- Sentence B: "Phương trình bậc hai có hai nghiệm phân biệt."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn không liên quan (thời tiết vs toán học).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine đo *góc* (hướng) giữa hai vector, bỏ qua độ dài, nên không bị ảnh hưởng bởi độ dài văn bản hay độ lớn vector; kết quả luôn nằm trong [-1, 1] nên dễ so sánh và xếp hạng. Euclidean lại nhạy với độ lớn vector, dễ bị lệch khi văn bản dài/ngắn khác nhau.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.1) = 23`
> Đáp án: **23 chunks**.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Với overlap=100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — tăng lên (do mỗi bước trượt ngắn lại nên cần nhiều chunk hơn). Muốn overlap nhiều hơn để giữ ngữ cảnh liền mạch giữa các chunk, tránh cắt đứt một ý/câu ngay ở ranh giới chunk khiến retrieval mất thông tin.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Kịch bản phim điện ảnh Việt Nam (Vietnamese film screenplays).

**Tại sao nhóm chọn domain này?**
> Kịch bản phim là văn bản dài, có cấu trúc rõ (cảnh, nhân vật, lời thoại) nên rất hợp để thử nghiệm các chiến lược chunking khác nhau. Mỗi phim là một chủ đề độc lập, dễ đặt câu hỏi có đáp án verify được, và metadata (thể loại, đạo diễn, năm) tạo điều kiện cho metadata filtering có ý nghĩa.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | bui_doi_cho_lon.md | PDF kịch bản (Charlie Nguyễn, 2013) | ~80,800 | genre=hanh_dong, year=2013, director=Charlie Nguyễn |
| 2 | co_gai_den_tu_hom_qua.md | PDF kịch bản (Phan Gia Nhật Linh, 2017) | ~132,500 | genre=hoc_duong, year=2017, director=Phan Gia Nhật Linh |
| 3 | nguoi_bat_tu.md | PDF kịch bản (Victor Vũ, 2018) | ~146,100 | genre=ky_ao, year=2018, director=Victor Vũ |
| 4 | nham_mat_thay_mua_he.md | PDF kịch bản (Cao Thúy Nhi, 2018) | ~120,200 | genre=lang_man, year=2018, director=Cao Thúy Nhi |
| 5 | thang_nam_ruc_ro.md | PDF kịch bản (Nguyễn Quang Dũng, 2018) | ~39,100 | genre=hoc_duong, year=2018, director=Nguyễn Quang Dũng |
| 6 | toi_thay_hoa_vang_tren_co_xanh.md | PDF kịch bản (Victor Vũ, 2015) | ~144,500 | genre=tam_ly, year=2015, director=Victor Vũ |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| doc_id | string | nguoi_bat_tu | Định danh để filter/xóa toàn bộ chunk của một phim. |
| title | string | NGƯỜI BẤT TỬ | Truy ngược chunk retrieve được về đúng tên phim. |
| genre | string | hoc_duong | Lọc theo thể loại (vd lấy phim học đường), tăng độ chính xác. |
| year | int | 2018 | Lọc/so sánh theo năm phát hành. |
| director | string | Victor Vũ | Lọc các phim cùng một đạo diễn. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Bụi Đời Chợ Lớn | FixedSizeChunker (`fixed_size`) | 539 | 199.8 | Kém — cắt cứng theo ký tự, dễ đứt giữa câu/cảnh |
| Bụi Đời Chợ Lớn | SentenceChunker (`by_sentences`) | 650 | 120.9 | Tốt theo câu nhưng chunk ngắn, ngữ cảnh hẹp |
| Bụi Đời Chợ Lớn | RecursiveChunker (`recursive`) | 465 | 171.7 | Tốt nhất — cắt theo ranh giới tự nhiên (đoạn/dòng/câu) |

*(Tham khảo thêm phim Cô Gái Đến Từ Hôm Qua: fixed_size 883 / sentences 1082 / recursive 836 chunk — cùng xu hướng: sentence nhiều chunk nhất, recursive ít nhất.)*

### Strategy Của Tôi

**Loại:** FixedSizeChunker (chunk_size=500, overlap=50)

**Mô tả cách hoạt động:**
> Cắt văn bản thành các đoạn cố định 500 ký tự bằng cửa sổ trượt; mỗi đoạn kề nhau chồng lấn 50 ký tự (bước trượt = 450). Đoạn cuối chứa phần còn lại; nếu văn bản ngắn hơn chunk_size thì trả về nguyên đoạn. Strategy không quan tâm dấu câu hay cấu trúc, chỉ đếm ký tự.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Kịch bản phim rất dài và định dạng không đồng nhất (lời thoại, mô tả cảnh, số trang). FixedSize cho độ dài chunk đều → embedding ổn định, dễ làm baseline để so sánh; overlap 50 giữ một phần ngữ cảnh ở ranh giới. Đây là lựa chọn đơn giản, nhanh, làm mốc đối chiếu cho các strategy phức tạp hơn của thành viên khác.

**Code snippet (nếu custom):** Không phải custom — dùng `FixedSizeChunker` có sẵn trong `src/chunking.py`.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Bụi Đời Chợ Lớn | best baseline (recursive) | 465 | 171.7 | Giữ ngữ cảnh tốt hơn, chunk theo ranh giới tự nhiên |
| Bụi Đời Chợ Lớn | **của tôi (fixed 500/50)** | 539 | 199.8 | Retrieval tổng 5/10; chunk đều nhưng cắt ngang câu làm loãng ngữ cảnh |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lê Xuân Tiến Đạt | FixedSize 500/50 | 5/10 | Đơn giản, chunk đều, metadata filter hoạt động tốt | Cắt ngang câu/cảnh → Q2, Q3 trượt |
| [Tên] | *(chờ kết quả thành viên)* | | | |
| [Tên] | *(chờ kết quả thành viên)* | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *(Điền sau khi tổng hợp điểm cả nhóm — so sánh FixedSize của tôi với Sentence/Recursive/custom của các bạn.)*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng regex `re.split(r"(?<=[.!?])\s+", text)` để tách câu tại vị trí sau dấu `.`, `!`, `?` có khoảng trắng theo sau; strip mỗi câu và bỏ câu rỗng. Sau đó gom mỗi `max_sentences_per_chunk` câu thành 1 chunk. Edge case: text rỗng/chỉ khoảng trắng → trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> `_split` thử lần lượt các separator theo thứ tự ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`). Base case: nếu đoạn đã ≤ chunk_size thì giữ nguyên; nếu hết separator (hoặc separator rỗng) thì cắt cứng theo cửa sổ ký tự. Với separator hiện tại, tách rồi gộp các mảnh nhỏ kề nhau tới sát chunk_size, mảnh nào vẫn quá to thì đệ quy xuống separator tiếp theo.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mỗi Document được chuyển thành 1 record chuẩn hóa `{id, doc_id, content, embedding, metadata}` qua `_make_record`, trong đó `embedding = embedding_fn(content)`; record được append vào list in-memory. `search` embed query rồi tính dot product giữa vector query và mọi embedding đã lưu, sắp xếp giảm dần theo score và trả về top_k (mock embeddings đã chuẩn hóa nên dot product = cosine).

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc **trước** theo metadata (giữ record khớp tất cả cặp key-value trong filter), rồi mới chạy similarity search trên tập đã lọc → tránh trả về chunk ngoài phạm vi. `delete_document` giữ lại các record có `doc_id` khác id cần xóa và trả `True` nếu kích thước store giảm.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve top_k chunk từ store, ghép phần `content` của chúng thành khối context (mỗi chunk 1 gạch đầu dòng). Build prompt gồm: chỉ dẫn ("chỉ trả lời dựa trên context") + context + câu hỏi, rồi truyền vào `llm_fn` và trả về kết quả. Nếu không retrieve được gì thì context ghi rõ "(no relevant context found)".

### Test Results

```
============================= 42 passed in 0.10s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Con chó đang chạy trong sân. | Con cún đang chạy trong vườn. | high | -0.090 | Sai |
| 2 | Tôi rất thích xem phim điện ảnh Việt Nam. | Tôi yêu những bộ phim của Việt Nam. | high | 0.053 | Sai |
| 3 | Hôm nay trời mưa rất to. | Kéo đặt máy tính lại cho gần. | low | 0.237 | Sai |
| 4 | Người Bất Tử là phim kỳ ảo. | Tháng Năm Rực Rỡ là phim học đường. | low | 0.029 | Đúng |
| 5 | Học sinh đến trường mỗi sáng. | Các em học sinh đi học mỗi ngày. | high | 0.222 | Đúng một phần |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Bất ngờ nhất là cặp 3 (hai câu hoàn toàn không liên quan) lại có điểm cao nhất (0.237), trong khi cặp 1 và 2 (đồng nghĩa rõ ràng) lại rất thấp, thậm chí âm. Lý do: lab đang dùng **mock embedding** — nó băm văn bản bằng md5 rồi sinh vector giả ngẫu nhiên, **không hề biểu diễn ngữ nghĩa**. Điều này cho thấy chất lượng similarity phụ thuộc hoàn toàn vào embedding model: muốn cosine phản ánh đúng nghĩa thì phải dùng embedder thật (sentence-transformers / OpenAI), không thể trông cậy vào mock.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Nhân vật chính trong *Tôi Thấy Hoa Vàng Trên Cỏ Xanh* là ai? | Thiều, Tường và Mận. |
| 2 | Chủ đề phim *Bụi Đời Chợ Lớn* là gì? | Những cuộc giao tranh đẫm máu giữa các băng nhóm giang hồ tại Chợ Lớn. |
| 3 | Bối cảnh tình yêu trong *Nhắm Mắt Thấy Mùa Hè* diễn ra ở đâu? | Thị trấn Higashikawa, Hokkaido, Nhật Bản. |
| 4 | Khả năng đặc biệt trong *Người Bất Tử* là gì? | Khả năng sống bất tử qua nhiều thế kỷ nhờ bùa ngải. |
| 5 | Phim nào có bối cảnh học sinh? *(câu này cần test filter `genre=hoc_duong`)* | Tháng Năm Rực Rỡ và Cô Gái Đến Từ Hôm Qua. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nhân vật chính *Hoa Vàng* | Đoạn thoại từ *Cô Gái Đến Từ Hôm Qua* | 0.465 | Có nhưng ở rank 3 | Không bám đúng chunk (top-1 sai phim) |
| 2 | Chủ đề *Bụi Đời Chợ Lớn* | Đoạn thoại từ *Cô Gái Đến Từ Hôm Qua* | 0.401 | Không có trong top-3 | Ungrounded — context sai phim |
| 3 | Bối cảnh *Nhắm Mắt Thấy Mùa Hè* | Đoạn từ *Tôi Thấy Hoa Vàng* | 0.401 | Không có trong top-3 | Ungrounded — context sai phim |
| 4 | Khả năng *Người Bất Tử* | Đoạn từ *Người Bất Tử* (Hùng, Duyên) | 0.389 | Có ở rank 1 | Bám đúng context phim Người Bất Tử |
| 5 | Phim bối cảnh học sinh *(filter)* | Đoạn từ *Cô Gái Đến Từ Hôm Qua* | 0.352 | Có (cả top-3 đều genre hoc_duong) | Bám đúng — filter giới hạn về phim học đường |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5  *(Q1, Q4, Q5; tổng điểm Retrieval Quality = 5/10)*

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
