# BẮT ĐẦU Ở ĐÂY — ChemiProof (Tiếng Việt)

## Bạn đang xây dựng dự án gì?

Bạn đang phát triển **một hệ thống nghiên cứu về gian lận dầu olive dựa trên tín hiệu quang phổ huỳnh quang**. Đầu vào là file đo quang phổ EEM từ phòng lab, **không phải ảnh chai dầu olive**. Đầu ra nghiên cứu là ước lượng **tỷ lệ thể tích dầu olive trong hỗn hợp** và báo cáo mức độ đáng tin của dự đoán.

**Ví dụ để hiểu đơn vị:** nếu kết quả minh họa là 0.78, điều đó tương ứng 78% *olive-oil volume fraction* theo quy ước mục tiêu, **không có nghĩa mô hình xác nhận dầu đó “thật 78%” theo tiêu chuẩn pháp luật**. Sai số và độ tin cậy phải được đánh giá bằng thí nghiệm trước khi hiển thị.

## Vì sao dự án này có giá trị?

- **Food chemistry:** học về fluorescence, chất phát huỳnh quang trong dầu và sự khác nhau giữa phản ứng hóa học/đo lường với mô hình thống kê.
- **Food authenticity:** bài toán xác định pha trộn; không đánh đồng pha trộn trong một nghiên cứu có chủ đích với hành vi gian lận thương mại.
- **Data science:** làm dữ liệu sạch, chia tập đúng cách, kiểm định và trực quan hóa.
- **Research:** thử nghiệm liệu mô hình có hoạt động khi xuất hiện loại dầu pha trộn chưa thấy lúc train không.
- **Responsible AI:** nếu dữ liệu lạ, mô hình phải có khả năng báo “không đủ cơ sở” thay vì đưa ra kết quả chính xác giả tạo.

## 6 thuật ngữ cần hiểu

1. **EEM:** ma trận cường độ huỳnh quang đo ở các cặp bước sóng kích thích/phát xạ. Dataset nghiên cứu có 35 × 270 ô tín hiệu.
2. **Sample:** một phép đo .dat, khác với một brand hoặc nồng độ.
3. **Target y:** tỷ lệ *thể tích* dầu olive trong hỗn hợp, không phải tỷ lệ khối lượng.
4. **Regression:** dự đoán một con số liên tục, khác classification phát hiện “có/không”.
5. **LOAO:** giữ lại TOÀN BỘ một loại dầu pha trộn để test; train trên các loại còn lại.
6. **Transductive OT:** phương pháp dùng dữ liệu quang phổ **không có nhãn** của nhóm test để điều chỉnh biểu diễn; không được sử dụng y của test để train hoặc chọn hyperparameter.

Xem thêm bản roadmap tổng quan bằng tiếng Việt: [`docs/vi/ROADMAP_VI.md`](ROADMAP_VI.md).

## Lộ trình đọc

| Tình huống | Đọc tài liệu |
|---|---|
| Muốn hiểu sản phẩm phục vụ ai | `docs/product/01_PRD.md` |
| Muốn hiểu khoa học và giả thuyết | `docs/science/02_RESEARCH_PROTOCOL.md` |
| Muốn biết dataset có gì | `docs/science/03_DATA_CONTRACT.md` |
| Muốn giao Claude Code lập trình | `CLAUDE.md`, `docs/engineering/04_ARCHITECTURE.md` |
| Muốn làm theo từng tuần | `docs/project/06_MILESTONES.md` |
| Muốn biết kết quả nào “đạt” | `docs/engineering/07_ACCEPTANCE_TESTS.md` |
| Muốn làm sản phẩm trông đẹp | `docs/product/08_UX_SPEC.md` |
| Muốn thêm dashboard Power BI cho góc nhìn QA/QC | `docs/bi/18_POWER_BI_SPEC.md` (đặc tả, chưa xây) |

## Về Power BI (mốc M6.5, tùy chọn)

Power BI là công cụ trình bày bảng điều khiển (dashboard). Trong dự án này nó **chỉ hiển thị kết quả đã được Python kiểm chứng**, không tự huấn luyện mô hình và không đưa ra kết luận gian lận hay an toàn. Lưu ý cho người dùng macOS: **Power BI Desktop chỉ chạy trên Windows**; tài khoản Gmail cá nhân thường không đăng ký được dịch vụ Power BI trên web (Desktop thì không cần đăng nhập). Hiện mới có đặc tả và hợp đồng dữ liệu, **chưa có file dashboard nào**.

## Cách dùng với Claude Code

1. Tạo repository mới tên `ChemiProof` (nên tách khỏi repository profile `MIA290306`).
2. Copy nguyên thư mục tài liệu vào repository. Mở thư mục repo bằng terminal/VS Code.
3. Chạy Claude Code tại **root** của repository để agent đọc `CLAUDE.md`.
4. Dán nguyên prompt ở `docs/engineering/12_AI_PROMPTS.md`, bắt đầu **PROMPT 0**.
5. Sau mỗi milestone, **đọc báo cáo thật**, mở các file output và đánh dấu checklist. Không chấp nhận “done” chỉ vì agent nói done.

## Ghi nhớ trước khi làm

- **Bộ tài liệu này chưa tải dataset, chưa train, chưa triển khai app.**
- Paper có kết quả rất cao nhưng chúng ta phải đánh giá lại độc lập và báo cáo mọi sai khác.
- `330` mẫu có phân bổ không đều: soybean 60, peanut 60, rapeseed 90, corn 90, walnut 30. Brand cũng không cân bằng. Đó là một rủi ro cần phân tích.
- Không tải file .dat tùy ý rồi coi mọi file có cùng định dạng. Bước M1 phải xác nhận header, trục, đơn vị, missing values, tên file và cấu trúc bên trong archive.
- Không đăng mã nguồn nghiên cứu của người khác như code của mình. Khi tham khảo cần ghi nguồn.

## Mốc thành công thực tế

- **Thành công bước đầu:** parse được archive, kiểm tra đúng sample inventory, tạo đồ thị EEM thật từ dữ liệu.
- **MVP nghiên cứu:** chạy 5-fold LOAO có MAE/RMSE/R² thật cho baseline, có scripts tái lập.
- **WOW thực sự:** so sánh cách hệ thống từ chối dự đoán trên mẫu rủi ro với lợi ích giảm sai số, có thí nghiệm đối chứng và thảo luận giới hạn.

## Sẵn sàng bắt đầu?

**Mốc tiếp theo là M0**: setup repo, tooling, deterministic tests và baseline tài liệu nguồn. Không bắt agent xây giao diện trước khi pipeline nghiên cứu hoạt động.
