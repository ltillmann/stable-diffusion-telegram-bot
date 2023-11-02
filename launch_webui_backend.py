#!/bin/bash

import subprocess
import socket
import sys
import time
import traceback

def main():
	try:
		#start webui backend
		p = subprocess.call(["bash webui.sh "
							  "--skip-torch-cuda-test "
							  "--api "
							  #"--nowebui "
							  "--listen "
							  "--precision full "
							  "--no-half "
							  "--use-cpu all "
							  "--lowvram "
							  "--allow-code "
							  #"--gradio-queue "
							  #"--controlnet-dir /Users/Lukas/Desktop/stablediff/stable-diffusion-webui/extensions/sd-webui-controlnet/models "
							  #"--no-half-controlnet "
							  "--ckpt-dir file.safetensors" # add your checkpoint path
							  ],
							 shell=True,
							 cwd="" # add your working directory
							)

	except KeyboardInterrupt as e:
		print('\nYou pressed Ctrl+C! Exiting...\n')
		sys.exit(0)

	except Exception as e:
		traceback.print_exc()
		sys.exit(0)

# main
if __name__ == "__main__":
	main()
