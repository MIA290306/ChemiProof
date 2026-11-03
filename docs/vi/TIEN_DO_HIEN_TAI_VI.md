# Tiến độ hiện tại của ChemiProof (bản bàn giao cho cộng tác viên)

**Cập nhật:** 2026-11-03 · **Người đọc:** Bruce1508 (cộng tác viên mới) · **Chủ dự án:** Mia Ho
Đây là bản tóm tắt. Nguồn sự thật chi tiết là `docs/project/14_PROGRESS_LOG.md` (bằng chứng từng milestone) và `docs/project/13_DECISION_LOG.md` (các quyết định phương pháp, ADR). Nếu bản này lệch với hai file đó, tin hai file đó.

## 1. Dự án là gì (30 giây)

ChemiProof ước lượng **tỷ lệ thể tích dầu olive** (số từ 0 đến 1) trong hỗn hợp dầu từ phổ huỳnh quang EEM (35 × 270 ô), và kiểm tra mô hình có biết khi nào nó không đáng tin. Đây là **dự án nghiên cứu**, không phải bài kiểm tra chứng nhận thực phẩm. Dữ liệu: Sun et al. (2026), Zenodo 19755088, CC BY 4.0, 330 mẫu, 5 loại dầu pha trộn (đậu nành, lạc, cải, ngô, óc chó).

Câu hỏi khoa học chính: khi gặp **một loại dầu pha trộn chưa từng thấy lúc huấn luyện** (LOAO: giữ lại toàn bộ một loại để kiểm tra), mô hình sai bao nhiêu?

## 2. Tiến độ theo milestone

| Milestone | Trạng thái | Ý nghĩa |
|---|---|---|
| M0 Nền tảng | REVIEW REQUIRED | Gói Python, CLI, config, CI |
| M1 Kiểm tra dữ liệu | REVIEW REQUIRED | 330/330 file đọc được, nhãn `a/11`, bảng kiểm kê |
| M2 Baseline hóa trắc học | REVIEW REQUIRED | SVR, PCA+SVR, PLS (chỉ nội bộ nguồn) |
| M3 Benchmark LOAO | REVIEW REQUIRED | 5 fold ngoài, đóng băng giao thức `LOAO-v1` |
| M4 Tái lập OT | REVIEW REQUIRED | Optimal transport (transductive), `LOAO-OT-v1` |
| M5 Từ chối dự đoán và độ bền | REVIEW REQUIRED | `LOAO-UQ-v1` (ADR-017) |
| M6 Giao diện nghiên cứu (Streamlit) | **CHƯA BẮT ĐẦU** | Kế hoạch đã có, chờ chủ dự án chốt (mục 5) |
| M6.5 Power BI | CHƯA BẮT ĐẦU (chỉ có đặc tả) | Cần M5, M6 và máy Windows |
| M7 Phát hành | CHƯA BẮT ĐẦU | |

"REVIEW REQUIRED" nghĩa là agent đã làm xong và có bằng chứng, **chỉ chủ dự án mới được đánh ACCEPTED**. Đừng tự đổi trạng thái này.

## 3. Kết quả đo được (tóm tắt, đơn vị: pp = điểm phần trăm, 1 pp = 0,01 phân số)

Trung bình không trọng số trên 5 chất pha trộn bị giữ lại, tính trên cả 330 mẫu. Số đầy đủ và theo từng fold nằm trong `results/`.

| Nội dung | Kết quả |
|---|---|
| Baseline inductive (M3) | `svr_raw` MAE 8,37 pp (R² 0,831); `pls` 6,50 pp (R² 0,903); `pca_svr` 16,55 pp (R² 0,019) |
| OT, transductive (M4) | `ot_svr` MAE 4,09 pp (R² 0,964). Trùng số đã công bố trong 0,001, nhưng chỉ khi batch đích có cùng phân bố nhãn với nguồn |
| Điểm yếu của OT | Batch lệch nhãn hoặc chỉ 10 phổ: OT sụp đổ (R² khoảng −3) hoặc không hơn mô hình không thích nghi |
| Từ chối dự đoán (M5) | Giữ 80%: PLS từ 6,50 xuống 6,22 pp, chỉ 3/5 fold cải thiện. **Không đáng tin cậy** trên benchmark này |
| Khoảng dự đoán 90% (M5) | Độ phủ quan sát được 0,47 đến 1,00 tùy chất pha trộn. Không có đảm bảo khi gặp chất lạ |
| Nhiễu, dịch nền, đổi thang | Dịch nền và đổi thang không đổi gì (do tiền xử lý). Nhiễu 1% làm MAE của PLS lên 17,7 pp |

Các số đã công bố của tác giả (raw 0,831; PCA 0,693; OT 0,965) được lưu **tách riêng**, không bao giờ gộp với số của chúng ta.

## 4. Quy tắc bất biến (không được vi phạm)

Đọc đầy đủ trong `CLAUDE.md`. Tóm lại:

1. Mục tiêu là phân số olive trong [0, 1]; quy ước nhãn `olive_fraction = a/11` cho thư mục `a：b` (ADR-008).
2. **Không rò rỉ nhãn đích**: mọi thứ fit (tiền xử lý, PCA, ngưỡng, hiệu chỉnh) chỉ dùng dữ liệu nguồn.
3. Không trộn kết quả **inductive** (một file) với **transductive** (cần cả batch phổ không nhãn).
4. Benchmark chính luôn là 5 fold LOAO. Không dùng chia mẫu ngẫu nhiên làm bằng chứng tổng quát hóa.
5. Từ chối dự đoán là tín hiệu nghiên cứu, **không phải kết luận an toàn hay "gian lận"**.
6. Không commit dữ liệu thô, mã của tác giả, hay khóa bí mật.
7. Giao thức đã đóng băng (`LOAO-v1`, `LOAO-OT-v1`, `LOAO-UQ-v1`) chỉ được đổi bằng giao thức mới và ADR mới.
8. Không bịa số liệu. Chưa chạy thì ghi **NOT RUN**.

## 5. Việc đang chờ và việc có thể làm tiếp

**Chờ chủ dự án quyết:**
- Duyệt ADR-014, 015, 016, 017 và đánh dấu ACCEPTED cho M0–M5.
- M6 cần một **mô hình cuối cùng huấn luyện trên cả 330 mẫu** (đề xuất PLS) cho trang "Screen Sample". Cần viết ADR-018 trước khi huấn luyện, và phải ghi rõ mô hình này không có đánh giá độc lập.

**Việc có thể nhận (chọn một, báo trước để không đụng nhau):**
- Kiểm tra kết quả M3–M5 độc lập: đọc `validation_report.md` của từng run trong `results/` và tìm lỗi.
- M5 còn dở: kiểm định hiệu ứng thương hiệu (lỗi lớn nằm ở soybean–olivera) và bộ phát hiện batch lệch nhãn cho OT. Cả hai cần ADR mới.
- Sau khi chủ dự án chốt: M6 (giao diện Streamlit).
- Phần xuất dữ liệu cho Power BI (CP-651 đến 653) chạy được trên Mac, nhưng chỉ làm sau M5/M6 được duyệt. Dựng dashboard cần Windows.

## 6. Cách chạy lại trên máy bạn

```bash
git clone https://github.com/MIA290306/ChemiProof.git
cd ChemiProof
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check . && pytest -q          # test dùng dữ liệu tổng hợp, không cần dữ liệu thật
chemiproof --help
```

**Dữ liệu thật** (96 MB) không nằm trong repo. Tải từ Zenodo 19755088 và đặt vào `data/raw/extracted` (đã bị git-ignore). Các test cần dữ liệu thật chạy bằng `pytest -m dataset`.

Chạy lại các thí nghiệm đã đóng băng:
```bash
chemiproof experiment run --config config/experiments/baseline.yaml          # M3
chemiproof experiment run --config config/experiments/ot_transductive.yaml  # M4
chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml  # M5
```
Các config có `run_class: locked` chỉ chạy khi cây git sạch (đã commit hết). Muốn thử nghiệm thì copy ra bản `exploratory`. Mọi lần chạy đều được ghi vào `results/experiment_registry.csv`.

## 7. Quy trình làm việc chung

- Làm trên nhánh riêng, mở pull request vào `main`, CI (ruff + pytest) phải xanh. Chưa bật bảo vệ nhánh `main`.
- Đừng thêm dòng `Co-Authored-By` vào commit hoặc PR (yêu cầu của chủ dự án).
- Mỗi thay đổi phương pháp cần một mục ADR trong `docs/project/13_DECISION_LOG.md`. Mỗi lần xong việc, cập nhật `14_PROGRESS_LOG.md` với lệnh thật, mã thoát và đường dẫn kết quả.
- Đọc theo thứ tự: `docs/vi/START_HERE_VI.md`, `CLAUDE.md`, `docs/project/06_MILESTONES.md`.

## 8. Giới hạn cần nhớ khi nói về dự án

Chỉ 5 hệ thống đích; một thiết bị, một phòng lab; hỗn hợp tạo trong lab, không phải sản phẩm ngoài chợ; thương hiệu dầu olive mất cân bằng (walnut chỉ có một thương hiệu). Kết quả tốt trên benchmark này không chứng minh dùng được ngoài thực tế.
