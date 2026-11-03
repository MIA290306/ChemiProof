# Mini Textbook — Food Chemistry + ML (cho sinh viên Food Science)

## A. Tín hiệu thực sự đến từ đâu?

Một mẫu dầu có các thành phần hóa học hấp thụ/phát huỳnh quang dưới kích thích thích hợp. Máy quang phổ lần lượt kích thích ở các bước sóng nhất định và đọc ánh sáng phát ra. **EEM** đặt bước sóng kích thích trên một trục, phát xạ trên trục còn lại, còn mỗi ô là tín hiệu đo được. Trong nghiên cứu này, mỗi EEM có 35 × 270 = **9.450** giá trị tín hiệu; không phải 9.450 mẫu độc lập.

Không được kết luận “đỉnh ở bước sóng X chắc chắn là phân tử Y” chỉ từ tương quan ML. Thiết bị, môi trường, nồng độ và các fluorophore có phổ chồng lấn có thể ảnh hưởng tín hiệu.

## B. Regression khác classification

**Regression** dự đoán một số, ví dụ olive fraction = `0.80` (80% theo thể tích). **Classification** dự đoán nhãn như “authentic/adulterated”. ChemiProof chọn regression vì dataset cung cấp tỷ lệ pha trộn biết trước. Mọi ngưỡng quyết định tuân thủ pháp luật cần xác minh độc lập, không tự đặt trong UI.

## C. Tại sao không random split?

Nếu cùng một loại dầu pha trộn, cùng brand và nồng độ xuất hiện ở cả train/test, mô hình có thể trông rất chính xác nhưng chỉ do “gặp dữ liệu gần giống”. LOAO giữ **nguyên một loại adulterant** ngoài train để kiểm tra năng lực gặp miền dữ liệu mới. Có 5 fold; chúng ta cần xem **từng fold** vì walnut chỉ 30 mẫu và một EVOO brand, trong khi rapeseed/corn 90 mẫu và ba brand.

## D. Optimal transport đơn giản

Hãy tưởng tượng biểu diễn phổ của các mẫu dầu được phân bố thành hai đám mây: miền nguồn (4 loại dầu đã biết) và miền đích (1 loại dầu lạ). **Optimal transport** xây dựng phép ghép giữa các phân bố để điều chỉnh điểm nguồn gần hơn phân bố đích. Sau đó hồi quy vẫn học trên **nhãn của nguồn**, nhưng đặc trưng đã được căn chỉnh.

Tại sao cần nhiều mẫu đích? Vì muốn biết “đám mây phân bố đích” phải có **một nhóm spectra**. Nếu chỉ upload một file, đó là tình huống khác, và không được gắn kết quả OT batch vào nó.

## E. Preprocessing

- **Baseline correction:** xử lý phần nền không liên quan tới chất phân tích; phải chọn thuật toán có cơ sở.
- **Savitzky–Golay:** làm mượt tín hiệu theo trục bước sóng bằng fit đa thức cục bộ; tham số quá lớn có thể làm mất đỉnh.
- **Normalization:** đưa mức cường độ về quy mô so sánh được; có thể loại bỏ thông tin hữu ích nếu lạm dụng.
- **PCA:** tìm trục biến thiên chính, giảm số chiều nhưng không mặc định tốt hơn.
- **SVR:** thuật toán hồi quy tìm hàm phù hợp với tolerance `epsilon`; đơn vị epsilon phụ thuộc đơn vị y nên cần kiểm tra.

## F. MAE, RMSE, R² hiểu sao?

- **MAE:** sai lệch tuyệt đối trung bình. Nếu MAE=0.05 *fraction* thì sai số trung bình là **5 percentage points** (giả định minh họa).
- **RMSE:** phạt sai số lớn nặng hơn, nên giúp phát hiện lỗi nghiêm trọng.
- **R²:** so sánh với mô hình dự đoán hằng số trong tập được chấm; có thể âm trên miền lạ. R² không phải “độ chính xác 96.5%”.
- **Bias:** chênh lệch trung bình có dấu; nếu positive, mô hình thường dự đoán nhiều olive hơn thực tế.

## G. OOD và abstention

**OOD** nghĩa là dữ liệu lệch so với tập tham khảo. Một điểm OOD cao chỉ là tín hiệu rủi ro, **không phải xác nhận rằng mẫu giả hoặc nguy hiểm**. **Abstention** cho phép từ chối đưa ra kết luận khi tính đáng tin thấp. Cần báo kèm tỉ lệ mẫu bị từ chối, nếu không ta có thể làm lỗi trung bình thấp chỉ bằng cách không dự đoán các trường hợp khó.

## H. Prediction interval

Khoảng ước lượng có thể được tạo từ lỗi hiệu chuẩn. Conformal prediction thông thường cần dữ liệu calibration và test có điều kiện phân bố tương tự (exchangeability). Khi đổi adulterant, điều kiện này có thể sai, do đó khoảng “90%” không có nghĩa nó chắc chắn bao phủ 90% mẫu lạ. Chỉ nói **empirical coverage** khi đã đo trên fold đó.

## I. Ba điều không được nhầm

1. **Tỷ lệ dầu olive trong mẫu** ≠ xác suất sản phẩm authentic.
2. **Mô hình trên dầu olive của dataset** ≠ mô hình cho mọi loại thực phẩm.
3. **Dự đoán có MAE tốt trong thử nghiệm** ≠ phép thử được cơ quan quản lý chứng nhận.

## J. Ba câu hỏi tự kiểm tra

1. Vì sao phải giữ hoàn toàn dầu walnut ra khỏi train trong một LOAO fold? (Đáp án: kiểm tra generalization trước loại adulterant chưa gặp.)
2. Một mô hình dự đoán `olive_fraction=0.75`. Nếu là binary volume blend, tỷ lệ adulterant suy ra bằng bao nhiêu? (Đáp án: 0.25 = 25%; chỉ trong mô hình binary blend.)
3. Vì sao không được nói prediction interval “90% guaranteed” trên adulterant chưa thấy? (Đáp án: phân bố bị shift, giả định exchangeability của standard conformal có thể không còn.)

## K. Power BI và lớp BI (mốc M6.5)

- **BI (business intelligence):** công cụ xem và tóm tắt kết quả bằng bảng, biểu đồ cho người làm QA/QC, không phải nơi huấn luyện mô hình.
- **Dashboard Power BI trong dự án:** chỉ đọc các bảng kết quả đã xuất từ Python; mỗi con số phải ghi rõ chạy nào (run), protocol nào, chế độ nào (inductive hay transductive).
- **Vì sao không trộn protocol:** kết quả LOAO inductive và OT transductive dùng lượng thông tin khác nhau; đặt chung một biểu đồ sẽ gây hiểu lầm.
- **Cờ "cần xem lại" (review required):** gợi ý nghiên cứu, **không** phải kết luận mẫu bị pha trộn.
- **Windows:** Power BI Desktop chỉ chạy trên Windows; dashboard chưa được coi là "đã xây" nếu chưa kiểm tra được ở đó.
