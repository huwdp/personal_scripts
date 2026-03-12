# Steps to run this
1. Run llama-server

E.g.
```
/home/huw/ai/llama.cpp/build/bin/llama-server -m /home/huw/ai/models/gemma-3-4b-it-Q4_K_M.gguf --mmproj /home/huw/ai/models/mmproj-model-f16.gguf -c 16384 -ngl 30 --alias vision-model --defrag-thold 0.1 --flash-attn on
```

You may need to change the command to suit your hardware.

2. Edit config

3. Run command
```
python create_tags.py
```

4. Review tag_database.json

5. Run command
```
python append_tags.py
```

# Requirements
Python
Pillow
piexif

Install in Terminal:
```
sudo apt install python3-pillow
sudo apt install python3-piexif
```