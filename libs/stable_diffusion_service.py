import requests
import base64
from PIL import Image
from io import BytesIO


class StableDiffusion:
    BASE_URL: str

    def __init__(self, base_url: str):
        self.BASE_URL = base_url

    def generate_image(
        self,
        dic: dict,
    ) -> list[Image.Image]:

        response = requests.post(
            f"{self.BASE_URL}/sdapi/v1/txt2img",
            json=dic,
        )
        response.raise_for_status()
        # print(response.json())
        data = response.json()
        if "images" not in data or not data["images"]:
            raise ValueError("No images returned from the API")
        image_base64_data = data["images"]
        images = []
        for img_data in image_base64_data:
            image_data = base64.b64decode(img_data)
            image = Image.open(BytesIO(image_data))
            images.append(image)
        return images
