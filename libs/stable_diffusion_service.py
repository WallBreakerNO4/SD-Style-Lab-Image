import requests
import base64
import asyncio
import aiohttp
from PIL import Image
from io import BytesIO


class GenerateImage:
    image: Image.Image
    parameters: dict
    info: str

    def __init__(self, image: Image.Image, parameters: dict, info: str):
        self.image = image
        self.parameters = parameters
        self.info = info


class StableDiffusion:
    BASE_URL: str

    def __init__(self, base_url: str, concurrency_limit: int = 3):
        self.BASE_URL = base_url
        self._concurrency_limit = concurrency_limit
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    async def aio_generate_images(
        self,
        dic: dict,
        index: int,
    ) -> tuple[list[GenerateImage], int]:
        """
        Asynchronously generate images using the Stable Diffusion API with concurrency control.
        """
        async with self._semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/sdapi/v1/txt2img",
                    json=dic,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if "images" not in data or not data["images"]:
                        raise ValueError("No images returned from the API")
                    image_base64_data = data["images"]
                    images = []
                    for img_data in image_base64_data:
                        image_data = base64.b64decode(img_data)
                        image = Image.open(BytesIO(image_data))
                        images.append(
                            GenerateImage(
                                image=image,
                                parameters=data.get("parameters", {}),
                                info=data.get("info", ""),
                            )
                        )
                    return images, index

    def generate_images(
        self,
        dic: dict,
    ) -> list[GenerateImage]:
        """
        Generate images using the Stable Diffusion API.
        """

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
            images.append(
                GenerateImage(
                    image=image,
                    parameters=data.get("parameters", {}),
                    info=data.get("info", ""),
                )
            )
        return images
