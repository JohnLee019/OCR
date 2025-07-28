from paddleocr import PaddleOCR
import cv2
import os

# PaddleOCR 객체 생성 (영어 또는 한국어 선택 가능)
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # 'en' → 영어, 'korean' → 한글

# 이미지 경로
image_path = 'result/english.jpeg'

# 파일 존재 확인
if not os.path.exists(image_path):
    print(f"[❌ 오류] 이미지 파일을 찾을 수 없습니다: {image_path}")
    exit(1)

# 이미지 로드
image = cv2.imread(image_path)

# OCR 실행
results = ocr.ocr(image_path, cls=True)

# 결과 추출
texts = []
for line in results[0]:
    box, (text, conf) = line
    texts.append(text)

# 결과 출력
print("📄 [텍스트 인식 결과]")
print('\n'.join(texts))

# 결과 저장
with open('result/paddle_ocr_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(texts))
print("✅ 텍스트가 ocr_result.txt에 저장되었습니다.")
