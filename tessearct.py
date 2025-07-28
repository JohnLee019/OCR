import pytesseract
import cv2
from PIL import Image
import os

# (Windows 사용자만) Tesseract 설치 경로 지정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지 경로
image_path = 'result/english.jpeg'  # 원하는 이미지 파일 경로로 변경

# 파일 존재 확인
if not os.path.exists(image_path):
    print(f"[❌ 오류] 이미지 파일을 찾을 수 없습니다: {image_path}")
    exit(1)

# 이미지 불러오기
image = cv2.imread(image_path)

# 흑백 변환 (OCR 정확도 향상)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# OCR 실행 (한국어)
text = pytesseract.image_to_string(gray, lang='eng')

# 결과 출력
print("📄 [텍스트 인식 결과]")
print(text)

# 결과 저장 옵션
with open('result/tesseract_ocr_result.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("✅ 텍스트가 ocr_result.txt에 저장되었습니다.")
