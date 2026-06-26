import argparse
import json
import os
import sys
import traceback


def load_payload(payload_path: str):
    with open(payload_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()

    try:
        payload = load_payload(args.payload)
        repo_dir = payload["repo_dir"]
        model_dir = payload["model_dir"]
        output_path = payload["output_path"]
        prompt_audio = payload["prompt_audio"]
        text = payload["text"]
        emo_audio_prompt = payload.get("emo_audio_prompt")
        emo_alpha = float(payload.get("emo_alpha", 1.0))

        if not os.path.isdir(repo_dir):
            raise FileNotFoundError(f"IndexTTS repo not found: {repo_dir}")
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"IndexTTS model dir not found: {model_dir}")
        if not os.path.exists(prompt_audio):
            raise FileNotFoundError(f"Reference audio not found: {prompt_audio}")
        if emo_audio_prompt and not os.path.exists(emo_audio_prompt):
            raise FileNotFoundError(f"Emotion reference audio not found: {emo_audio_prompt}")

        sys.path.insert(0, repo_dir)
        from indextts.infer_v2 import IndexTTS2

        cfg_path = os.path.join(model_dir, "config.yaml")
        tts = IndexTTS2(
            cfg_path=cfg_path,
            model_dir=model_dir,
            use_fp16=False,
            use_cuda_kernel=False,
            use_deepspeed=False,
            use_accel=False,
            use_torch_compile=False,
        )
        tts.infer(
            spk_audio_prompt=prompt_audio,
            text=text,
            output_path=output_path,
            emo_audio_prompt=emo_audio_prompt,
            emo_alpha=emo_alpha,
            verbose=False,
        )
        print(
            json.dumps(
                {
                    "output_path": output_path,
                    "prompt_text_received": bool(payload.get("prompt_text")),
                    "emo_audio_prompt_used": bool(emo_audio_prompt),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
