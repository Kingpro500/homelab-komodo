#!/bin/sh
# Bootstrap: kjøres ved hver oppstart, hopper over det som finnes. Ligger i repoet og kopieres til /models/start.sh.
set -e
cd /models; mkdir -p /models/tmp /models/pipcache
command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git curl libgl1 libglib2.0-0 >/dev/null; }
[ -d venv ] || python -m venv venv
[ -d ComfyUI ] || git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git
[ -f venv/.ok ] || { venv/bin/pip install -q torch torchvision torchaudio && venv/bin/pip install -q -r ComfyUI/requirements.txt && touch venv/.ok; }
dl() { [ -s "$2" ] || { mkdir -p "$(dirname "$2")"; curl -L --fail -o "$2.part" "$1" && mv "$2.part" "$2"; }; }
H=https://huggingface.co
M=ComfyUI/models
dl $H/nafishasan60/Darkbeast_Krea2v3/resolve/main/darkBeast330_int8convrot_heur.safetensors $M/diffusion_models/darkBeast330_int8convrot_heur.safetensors
dl $H/Comfy-Org/Krea-2/resolve/main/text_encoders/qwen3vl_4b_fp8_scaled.safetensors $M/text_encoders/qwen3vl_4b_fp8_scaled.safetensors
dl $H/Comfy-Org/Krea-2/resolve/main/vae/qwen_image_vae.safetensors $M/vae/qwen_image_vae.safetensors
[ -f venv/.viewer ] || { venv/bin/pip install -q fastapi uvicorn pillow python-multipart && touch venv/.viewer; }
dl https://huggingface.co/Comfy-Org/Krea-2/resolve/main/loras/krea2_turbo_lora_rank_64_bf16.safetensors $M/loras/krea2_turbo_lora_rank_64_bf16.safetensors
mkdir -p /models/gallery
(cd /models/viewer && exec /models/venv/bin/uvicorn app:app --host 0.0.0.0 --port 7860) &
exec venv/bin/python ComfyUI/main.py --listen 0.0.0.0 --port 8188 --lowvram --output-directory /models/output
