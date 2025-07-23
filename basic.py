import pyautogui
import pytesseract
from PIL import Image
import os
import cv2

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

path = 'C:/Users/User/Pictures/Screenshots/스크린샷(8).png'
os.path.isfile(path)

custom_config = r'--oem 3 --psm 6'



# screenshot = pyautogui.screenshot()


text = pytesseract.image_to_string(path, lang='kor+eng', config=custom_config)

print('Recognized Text:')
print(text)