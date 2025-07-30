from paddleocr import PaddleOCR
import os

# 1) OCR 객체 생성 (Deprecated warning 제거용 최신 옵션)
ocr = PaddleOCR(
    use_textline_orientation=False,      # 회전 감지 OFF
    use_doc_orientation_classify=False,  # 문서 방향 분류 OFF
    use_doc_unwarping=False,             # 문서 퍼스펙티브 보정 OFF
    lang='korean'                        # 한국어 모델
)

# 2) 이미지 경로 (현재 스크립트 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(BASE_DIR, 'test_image.png')

if not os.path.exists(img_path):
    print(f"❌ 이미지 파일을 찾을 수 없습니다: {img_path}")
    exit(1)

# 3) OCR 실행
raw = ocr.predict(img_path)

# 4) 텍스트 추출: 두 가지 케이스 모두 지원
texts = []

if isinstance(raw, list) and raw:
    first = raw[0]
    # Case A: JSON-like dict  → ['rec_texts'] 키 활용
    if isinstance(first, dict):
        for page in raw:
            texts.extend(page.get('rec_texts', []))
    # Case B: nested list-of-lists → [(box, (text,score)), ...]
    elif isinstance(first, list):
        for line in raw:
            for box_text in line:
                # box_text might be [box, text, score] or [box, (text,score)]
                if isinstance(box_text, list) and len(box_text) == 3:
                    # [box, text, score]
                    _, text, _ = box_text
                else:
                    # [box, (text,score)]
                    _, (text, _) = box_text
                texts.append(text)
else:
    print("⚠️ OCR 결과 형식을 알 수 없어 텍스트를 추출할 수 없습니다.")

# 5) 파일에 저장
output_dir = os.path.join(BASE_DIR, 'result')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'ocr_result.txt')

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(texts))

print(f"✅ OCR 완료 — 텍스트가 '{output_path}'에 저장되었습니다.")
