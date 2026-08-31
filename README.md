# Chinese → Vietnamese Video Translator V0.1

Mục tiêu của V0.1: video tiếng Trung → phụ đề SRT tiếng Việt.

## V0.1 làm gì?
1. Nhận video/audio.
2. Dùng Faster-Whisper nhận diện tiếng Trung.
3. Giữ timestamp theo từng đoạn.
4. Gửi từng đoạn sang backend dịch OpenAI-compatible.
5. Xuất `*_vi.srt`.

Chưa làm TTS/ghép video ở V0.1. Chỉ cần bước này chạy ổn rồi mới nâng cấp.

## Cài đặt
```bash
pip install -r requirements.txt
```
Cần FFmpeg trong PATH.

## Chạy
```bash
python -m app.main input.mp4 --output output_vi.srt
```

Biến môi trường:
- `TRANSLATOR_API_KEY`: API key của backend dịch.
- `TRANSLATOR_BASE_URL`: mặc định `https://api.openai.com/v1`.
- `TRANSLATOR_MODEL`: mặc định `gpt-4o-mini`.

Whisper mặc định `small`, có thể đổi bằng `--whisper-model tiny|base|small|medium|large-v3`.

## Ghi chú
Bộ từ điển OCR/tên riêng được đặt tại `glossary.json`. Đây là lớp chuẩn hóa trước khi dịch để giảm lỗi tên nhân vật.
