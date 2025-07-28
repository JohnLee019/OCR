import cv2
import numpy as np

# 이미지 불러오기
img = cv2.imread('result/test.png')
result = img.copy()

# HSV 변환
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 컬러 텍스트 마스크 (모든 색상 + 회색)
color_mask = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([180, 255, 255]))

# 추가 회색 톤까지 처리하기 위한 grayscale 마스크
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 255에 가까운 흰색은 제외하고, 회색 글자 영역만 잡기
gray_mask1 = cv2.inRange(gray, 50, 200)   # 중간 회색까지 포함

# 두 마스크 결합
combined_mask = cv2.bitwise_or(color_mask, gray_mask1)

# 해당 마스크 영역을 검정색으로 덮기
result[combined_mask > 0] = [0, 0, 0]

# 결과 저장
cv2.imwrite('result/output_black_perfect.png', result)
print("✅ 완벽한 검정 텍스트 변환 완료: output_black_perfect.png")
