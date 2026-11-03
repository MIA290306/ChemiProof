# CHEMIPROOF — ROADMAP THỰC HIỆN (TIẾNG VIỆT)

**Bản kế hoạch:** 24/10/2026 · **Trạng thái:** CHƯA LẬP TRÌNH / CHƯA CÓ KẾT QUẢ MODEL

Mục tiêu: dùng dữ liệu EEM fluorescence đo từ dầu olive pha trộn để **ước lượng tỷ lệ dầu olive theo thể tích**, thử nghiệm cách mô hình hoạt động khi gặp một loại dầu pha trộn mới, và đánh giá khi nào nên từ chối dự đoán. Đây là dự án nghiên cứu hỗ trợ screening, **không phải công cụ kết luận gian lận hay chứng nhận pháp lý**.

## Các milestone và bằng chứng phải xem

| Giai đoạn | Bạn sẽ học được gì | Claude Code phải làm | Bằng chứng bạn phải kiểm tra |
|---|---|---|---|
| **M0 — Foundation** | Git, Python, môi trường ảo, test | Tạo repo cấu trúc chuẩn, setup package, test CI, synthetic fixtures | `pytest` PASS thật, CLI help, file config, không fake số liệu |
| **M1 — Dataset Audit** | EEM, nồng độ %, đọc tín hiệu lab | Lấy dữ liệu chính thức, kiểm tra `.dat`, lập manifest và heatmap thật | Tổng 330 hoặc biên bản sai khác; phân nhóm 60/60/90/90/30; labels đúng chiều; đồ thị có sample ID |
| **M2 — Baselines** | Preprocessing, regression, MAE/RMSE/R² | Làm pipeline chuẩn và mô hình mean, SVR, PCA-SVR/PLS | Mô hình có điểm đánh giá nguồn thật, trục bước sóng đúng, không leakage |
| **M3 — LOAO** | Generalization, chia dữ liệu khoa học | Thử cả 5 holdout oil groups; train/tune chỉ từ 4 nhóm nguồn | 5 bảng điểm theo nhóm và 1 bảng tổng hợp macro + pooled, phân tích brand imbalance |
| **M4 — OT Replication** | Optimal Transport, miền nguồn/miền đích | Căn chỉnh phổ nguồn theo batch test không nhãn rồi dự đoán | Kết quả và khác biệt so với paper, log OT convergence, không dùng nhãn target để train |
| **M5 — Trustworthy AI** | Uncertainty, OOD, selective risk | Thêm quy tắc từ chối, đo error–coverage, thử nhiễu | Biểu đồ retention vs MAE, empirical interval coverage và các failure cases |
| **M6 — Research Explorer** | Kết nối khoa học với app | Streamlit hiển thị phổ, benchmark, upload, report | Demo hoạt động với dữ liệu thật; file lỗi bị từ chối; single vs batch rõ ràng |
| **M7 — Research Portfolio** | Viết báo cáo, khoa học tái lập | Research report, model card, README, demo, review | Người khác chạy lại được, có DOI/citations, không khẳng định kết quả chưa chứng minh |

## Cách tổ chức công việc với Claude Code

1. Giải nén toàn bộ thư mục dự án vào một repository GitHub mới (gợi ý tên `ChemiProof`). Không trộn vào repository profile `MIA290306`.
2. Mở folder này trong VS Code hoặc terminal. Cho Claude Code đọc `CLAUDE.md` trước khi ra lệnh.
3. Đưa prompt **PROMPT 0** trong `docs/engineering/12_AI_PROMPTS.md` cho agent để triển khai **M0**.
4. Sau khi agent nói xong, đọc bằng chứng test và milestone report. Đánh dấu `ACCEPTED` chỉ sau khi bạn tự kiểm tra.
5. Chuyển sang PROMPT 1/M1, tiếp tục tuần tự. Có blocker thì sửa blocker trước, không nhảy qua giai đoạn tiếp theo.

## Thế nào là nghiên cứu có “WOW factor” thật?

- Không phải thêm AI chatbot hoặc dashboard nhiều màu.
- Phải có câu hỏi nghiên cứu rõ: **Model có bị quá tự tin trên một adulterant chưa từng thấy không?**
- Phải có so sánh công bằng: mô hình thường vs batch-OT vs mô hình có khả năng từ chối.
- Phải có kết quả xấu/ngoại lệ được giải thích.
- Phải phân biệt **số paper công bố** với **số do ChemiProof tự đo**.
- Phải công bố giới hạn mẫu nhỏ, 5 domain và sự mất cân đối thương hiệu.

## Ba câu hỏi bạn nên tự trả lời trước mỗi milestone

1. Tôi đang kiểm tra giả thuyết khoa học nào?
2. Tôi cần chứng cứ gì để khẳng định bước này hoạt động?
3. Có điều gì làm kết quả trông tốt giả tạo (data leakage, chọn mẫu, sai nhãn, lựa chọn mô hình dựa trên test) không?

### Những file quan trọng nhất

- `docs/vi/START_HERE_VI.md` — bắt đầu từ zero.
- `CLAUDE.md` — kỷ luật làm việc cho AI coding agent.
- `docs/science/02_RESEARCH_PROTOCOL.md` — bài toán khoa học.
- `docs/project/06_MILESTONES.md` — yêu cầu đầy đủ từng giai đoạn.
- `docs/engineering/07_ACCEPTANCE_TESTS.md` — các bài test phải PASS.
- `docs/project/16_TASK_BACKLOG.md` — danh sách task có mã CP-xxx.
- `docs/project/14_PROGRESS_LOG.md` — tiến độ và bằng chứng thực tế.

**Quan trọng:** file ZIP documentation pack này không bao gồm bộ dữ liệu 96 MB, không bao gồm code từ paper và chưa có hệ thống ML chạy được. Đó là mục tiêu của các milestone tới.
