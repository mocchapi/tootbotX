import io
import json
import cv2
import numpy as np
import requests
def get_ocr(image,key_api,url_api="https://api.ocr.space/parse/image",language='eng'):
	image = str(image)
	img = cv2.imread(image, 1)
	height, width, _ = img.shape
	_, compressedimage = cv2.imencode(".jpg", img, [1, 90])
	file_bytes = io.BytesIO(compressedimage)
	result = requests.post(url_api,
				files = {"screenshot.jpg": file_bytes},
				data = {"apikey": key_api,
					"language": language})
	result = result.content.decode()
	result = json.loads(result)
	parsed_results = result.get("ParsedResults")[0]
	text_detected = parsed_results.get("ParsedText")
	return text_detected
