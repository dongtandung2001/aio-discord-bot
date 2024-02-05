import requests
from PIL import Image

import pytesseract

url = "https://cdn.discordapp.com/attachments/1118785038272712778/1203893764322631730/image.png?ex=65d2c070&is=65c04b70&hm=9ee0640ffcd954547221fb9c6136faea14c93de009bbded900fb1e32c4f1a584&"


r = requests.get(url, stream=True)

image = Image.open(r.raw)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(pytesseract.image_to_string(image))


