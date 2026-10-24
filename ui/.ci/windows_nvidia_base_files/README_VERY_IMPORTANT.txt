HOW TO RUN:

if you have a NVIDIA gpu:

run_nvidia_gpu.bat

if you want to enable the fast fp16 accumulation (faster for fp16 models with slightly less quality):

run_nvidia_gpu_fast_fp16_accumulation.bat


To run it in slow CPU mode:

run_cpu.bat



IF YOU GET A RED ERROR IN THE UI MAKE SURE YOU HAVE A MODEL/CHECKPOINT IN: ScalifyUI\models\checkpoints

You can download the stable diffusion 1.5 one from: https://huggingface.co/Khulnasoft/stable-diffusion-v1-5-archive/blob/main/v1-5-pruned-emaonly-fp16.safetensors


RECOMMENDED WAY TO UPDATE:
To update the ScalifyUI code: update\update_scalifyui.bat



To update ScalifyUI with the python dependencies, note that you should ONLY run this if you have issues with python dependencies.
update\update_scalifyui_and_python_dependencies.bat


TO SHARE MODELS BETWEEN SCALIFYUI AND ANOTHER UI:
In the ScalifyUI directory you will find a file: extra_model_paths.yaml.example
Rename this file to: extra_model_paths.yaml and edit it with your favorite text editor.
