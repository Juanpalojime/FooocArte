import torch
try:
    import clip
except ImportError:
    clip = None

class CLIPQualityFilter:
    def __init__(self, device="cuda"):
        if clip is None:
            print("[CLIP] Warning: openai-clip not installed. CLIP filter disabled.")
            self.model = None
            return

        try:
            self.model, self.preprocess = clip.load("ViT-B/32", device=device)
            self.device = device
        except Exception as e:
            print(f"[CLIP] Error loading model: {e}")
            self.model = None

    def score(self, image, prompt: str) -> float:
        if self.model is None:
            return 1.0 # Pass if model not loaded

        with torch.no_grad():
            try:
                # Expecting PIL image
                image_input = self.preprocess(image).unsqueeze(0).to(self.device)
                text_input = clip.tokenize([prompt]).to(self.device)

                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_input)

                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                return (image_features @ text_features.T).item()
            except Exception as e:
                print(f"[CLIP] Scoring error: {e}")
                return 1.0 # Pass on error to avoid blocking
