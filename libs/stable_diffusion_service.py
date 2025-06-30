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
        prompt: str = "",
        negative_prompt: str = "",
        styles: list[str] = [],
        seed: int = -1,
        subseed: int = -1,
        subseed_strength: float = 0,
        seed_resize_from_h: int = -1,
        seed_resize_from_w: int = -1,
        sampler_name: str = "string",
        scheduler: str = "string",
        batch_size: int = 1,
        n_iter: int = 1,
        steps: int = 50,
        cfg_scale: float = 7,
        distilled_cfg_scale: float = 3.5,
        width: int = 512,
        height: int = 512,
        restore_faces: bool = True,
        tiling: bool = True,
        do_not_save_samples: bool = False,
        do_not_save_grid: bool = False,
        eta: float = 0,
        denoising_strength: float = 0,
        s_min_uncond: float = 0,
        s_churn: float = 0,
        s_tmax: float = 0,
        s_tmin: float = 0,
        s_noise: float = 0,
        override_settings: dict = {},
        override_settings_restore_afterwards: bool = True,
        refiner_checkpoint: str = "string",
        refiner_switch_at: float = 0,
        disable_extra_networks: bool = False,
        firstpass_image: str = "string",
        comments: dict = {},
        enable_hr: bool = False,
        firstphase_width: int = 0,
        firstphase_height: int = 0,
        hr_scale: float = 2,
        hr_upscaler: str = "string",
        hr_second_pass_steps: int = 0,
        hr_resize_x: int = 0,
        hr_resize_y: int = 0,
        hr_checkpoint_name: str = "string",
        hr_additional_modules: list[str] = [],
        hr_sampler_name: str = "string",
        hr_scheduler: str = "string",
        hr_prompt: str = "",
        hr_negative_prompt: str = "",
        hr_cfg: float = 1,
        hr_distilled_cfg: float = 3.5,
        force_task_id: str = "string",
        sampler_index: str = "Euler",
        script_name: str = "string",
        script_args: list = [],
        send_images: bool = True,
        save_images: bool = False,
        alwayson_scripts: dict = {},
        infotext: str = "string",
    ) -> list[Image.Image]:

        response = requests.post(
            f"{self.BASE_URL}/sdapi/v1/txt2img",
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "styles": styles,
                "seed": seed,
                "subseed": subseed,
                "subseed_strength": subseed_strength,
                "seed_resize_from_h": seed_resize_from_h,
                "seed_resize_from_w": seed_resize_from_w,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "batch_size": batch_size,
                "n_iter": n_iter,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "distilled_cfg_scale": distilled_cfg_scale,
                "width": width,
                "height": height,
                "restore_faces": restore_faces,
                "tiling": tiling,
                "do_not_save_samples": do_not_save_samples,
                "do_not_save_grid": do_not_save_grid,
                "eta": eta,
                "denoising_strength": denoising_strength,
                "s_min_uncond": s_min_uncond,
                "s_churn": s_churn,
                "s_tmax": s_tmax,
                "s_tmin": s_tmin,
                "s_noise": s_noise,
                "override_settings": override_settings,
                "override_settings_restore_afterwards": override_settings_restore_afterwards,
                "refiner_checkpoint": refiner_checkpoint,
                "refiner_switch_at": refiner_switch_at,
                "disable_extra_networks": disable_extra_networks,
                "firstpass_image": firstpass_image,
                "comments": comments,
                "enable_hr": enable_hr,
                "firstphase_width": firstphase_width,
                "firstphase_height": firstphase_height,
                "hr_scale": hr_scale,
                "hr_upscaler": hr_upscaler,
                "hr_second_pass_steps": hr_second_pass_steps,
                "hr_resize_x": hr_resize_x,
                "hr_resize_y": hr_resize_y,
                "hr_checkpoint_name": hr_checkpoint_name,
                "hr_additional_modules": hr_additional_modules,
                "hr_sampler_name": hr_sampler_name,
                "hr_scheduler": hr_scheduler,
                "hr_prompt": hr_prompt,
                "hr_negative_prompt": hr_negative_prompt,
                "hr_cfg": hr_cfg,
                "hr_distilled_cfg": hr_distilled_cfg,
                "force_task_id": force_task_id,
                "sampler_index": sampler_index,
                "script_name": script_name,
                "script_args": script_args,
                "send_images": send_images,
                "save_images": save_images,
                "alwayson_scripts": alwayson_scripts,
                "infotext": infotext,
            },
        )
        response.raise_for_status()
        print(response.json())
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
