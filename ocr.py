from paddleocr import PaddleOCR, draw_ocr
import os
import paddle
from PIL import Image


# OCR 객체 생성
ocr = PaddleOCR(lang='korean', use_angle_cls=True)

# 이미지 경로
image_path = "C:/Users/User/Pictures/Screenshots/testimage.png"
result = ocr.ocr(image_path, cls=True)

for line in result:
    print(line)

image = Image.open(image_path).convert('RGB')
boxes = [line[0] for line in result]
txts = [line[1][0] for line in result]
scores = [line[1][1] for line in result]
im_show =  draw_ocr(image, boxes, txts, scores, font_path='./fonts/simfang.ttf')
im_show = Image.fromarray(im_show)
im_show.save('result.png')



# # 경로 확인
# if not os.path.exists(image_path):
#     raise FileNotFoundError(f"이미지 경로 확인 필요: {image_path}")

# # 예측 실행
# results = ocr.predict(image_path)

# # 결과 출력
# for res in results:
#     if hasattr(res, "rec_res"):
#         for text, confidence in res.rec_res:
#             print(f"[{confidence:.2f}] {text}")
