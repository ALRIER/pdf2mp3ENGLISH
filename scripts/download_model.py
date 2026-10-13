"""Preload the official Kokoro model in the Hugging Face cache (no weights committed)."""
import argparse
from kokoro import KPipeline

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voice", default="af_heart")
    args = p.parse_args()
    engine = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device="cpu")
    # Loading a voice triggers its own asset download as needed.
    generated = next(iter(engine("Model download verification.", voice=args.voice)))
    if generated[2] is None:
        raise RuntimeError("Model returned no audio")
    print(f"Kokoro model and {args.voice} voice ready for CPU inference.")

if __name__ == "__main__":
    main()
