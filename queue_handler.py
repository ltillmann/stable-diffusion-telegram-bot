import os
import base64
import requests
import numpy as np
from PIL import Image
from datetime import datetime
from scipy.ndimage import binary_dilation

from cloth_segmentation import segment_clothes
from huggingface_cloth_segmentation.process import get_mask

def queue_request(hashed_user_id, prompts):
    try:
        print(f"{datetime.now().isoformat(' ', 'seconds')} Preparing payload...\n")


        # payload
        payload = {
            #"sampler_index": "DPM++ SDE Karras",  # Euler, DPM++ SDE Karras
            "sampler_name": "DPM++ SDE Karras",
            "seed": -1, # random
            "prompt": prompts,  # user prompts
            "negative_prompt": "",
            "steps": 30,  #
            "cfg_scale": 7,  # higher settings will leave weird artefacts
            "denoising_strength": 0.75, #
            "width": 512, #512
            "height": 512,
        }


        # queuing request
        print(f"{datetime.now().isoformat(' ', 'seconds')} Transmitting to WebUI...\n")

        url = "http://127.0.0.1:7860"

        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload).json()

        return response

    except Exception as e:
        print(e)


def turnover_request(url):
    response = requests.get(url=f'{url}/queue/status').json()
    turnover_time = round(response.get("avg_event_process_time"), 5) #turnover time in minutes

    return turnover_time
