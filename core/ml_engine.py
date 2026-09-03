# import torch
# import timm
# import cv2
# import numpy as np
# import os
# from torchvision import transforms
# from PIL import Image
# from django.conf import settings

# # --- 1. CONFIGURATION ---
# NUM_CLASSES = 5
# IMG_SIZE = 300
# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/best_model_scientific.pth')

# # --- 2. THE "TUFF" PREPROCESSING  ---
# class RetinaPreprocessing:
#     def __call__(self, img):
#         img_np = np.array(img)
        
#         # Extract Green Channel
#         if img_np.ndim == 3 and img_np.shape[2] == 3:
#             g_channel = img_np[:, :, 1]
#         else:
#             g_channel = img_np 

#         # Apply CLAHE
#         clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#         enhanced_img = clahe.apply(g_channel)

#         # Stack back to 3 channels
#         final_img = np.stack([enhanced_img]*3, axis=-1)
#         return Image.fromarray(final_img)

# # --- 3. TRANSFORMS ---
# val_transform = transforms.Compose([
#     RetinaPreprocessing(),
#     transforms.Resize((IMG_SIZE, IMG_SIZE)),
#     transforms.ToTensor(),
#     transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
# ])

# # --- 4. LOAD MODEL (Singleton Pattern) ---
# _model = None

# def load_model():
#     global _model
#     if _model is None:
#         print(" Loading Ocular Model into Memory...")
#         _model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=NUM_CLASSES)
        
#         # Load weights (Map to CPU ensures it works even if server has no GPU)
#         try:
#             state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
#             _model.load_state_dict(state_dict)
#             _model.eval()
#             print("Model loaded successfully!")
#         except FileNotFoundError:
#             print(f"Error: Model file not found at {MODEL_PATH}")
#     return _model

# # --- 5. PREDICTION FUNCTION ---
# def predict_image(image_file):
#     model = load_model()
    
#     # Open image from Django InMemoryUploadedFile
#     img = Image.open(image_file).convert('RGB')
    
#     # Preprocess
#     input_tensor = val_transform(img).unsqueeze(0) # Add batch dimension
    
#     # Inference
#     try:
#         with torch.no_grad():
#             # Pass input_tensor to model
#             outputs = model(input_tensor)
#             probabilities = torch.nn.functional.softmax(outputs[0], dim=0).tolist()
            
#             # --- SENSITIVITY FIX ---
#             normal_index = 0 # Matches index 0 in your mapping below!
            
#             # Artificial Sensitivity Penalty: Reduce the Normal probability by 30% 
#             # to force the model to reveal hidden disease signals.
#             probabilities[normal_index] = probabilities[normal_index] * 0.70 
            
#             # Recalculate the winner after the penalty
#             max_prob = max(probabilities)
#             predicted_class_idx = probabilities.index(max_prob)
            
#             # Normalize the probabilities back to 100% so the UI looks clean
#             total_prob = sum(probabilities)
#             normalized_probs = [p / total_prob for p in probabilities]
            
#             final_confidence = normalized_probs[predicted_class_idx] * 100
#             # ---------------------------
            
#         # Map to Class Name
#         class_mapping = {
#             0: 'Normal', 
#             1: 'Glaucoma', 
#             2: 'Diabetic Retinopathy', 
#             3: 'Cataract', 
#             4: 'Age-related Macular Degeneration'
#         }
        
#         # Return the correctly formatted variables
#         return {
#             'diagnosis': class_mapping[predicted_class_idx],
#             'confidence': f"{final_confidence:.2f}%",
#             'all_probs': {k: f"{v*100:.1f}%" for k, v in zip(class_mapping.values(), normalized_probs)}
#         }
#     except Exception as e:
#         return {'diagnosis': 'Error', 'confidence': '0%', 'all_probs': {'Error': str(e)}}

import torch
import timm
import cv2
import numpy as np
import os
from torchvision import transforms
from PIL import Image
from django.conf import settings

# --- 1. CONFIGURATION ---
NUM_CLASSES = 5
IMG_SIZE = 300
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/best_model_scientific.pth')

# --- 2. THE "TUFF" PREPROCESSING  ---
class RetinaPreprocessing:
    def __call__(self, img):
        img_np = np.array(img)
        if img_np.ndim == 3 and img_np.shape[2] == 3:
            g_channel = img_np[:, :, 1]
        else:
            g_channel = img_np 
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_img = clahe.apply(g_channel)
        final_img = np.stack([enhanced_img]*3, axis=-1)
        return Image.fromarray(final_img)

# --- 3. TRANSFORMS ---
val_transform = transforms.Compose([
    RetinaPreprocessing(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# --- 4. GRAD-CAM WRAPPER CLASS ---
class GradCAMModel:
    def __init__(self, model):
        self.model = model
        self.gradients = None
        self.activations = None
        # Register hooks for the last convolutional layer of EfficientNet-B3
        self.model.conv_head.register_forward_hook(self.save_activations)
        self.model.conv_head.register_full_backward_hook(self.save_gradients)

    def save_activations(self, module, input, output):
        self.activations = output

    def save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate_heatmap(self, input_tensor, class_idx):
        self.model.zero_grad()
        output = self.model(input_tensor)
        score = output[0][class_idx]
        score.backward()

        # Weight activations by pooled gradients
        weights = torch.mean(self.gradients, dim=[0, 2, 3])
        for i in range(self.activations.size(1)):
            self.activations[:, i, :, :] *= weights[i]
        
        heatmap = torch.mean(self.activations, dim=1).squeeze()
        heatmap = np.maximum(heatmap.detach().cpu().numpy(), 0)
        heatmap = cv2.resize(heatmap, (IMG_SIZE, IMG_SIZE))
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        return heatmap

# --- 5. LOAD MODEL (Singleton Pattern) ---
_model_wrapper = None

def load_model():
    global _model_wrapper
    if _model_wrapper is None:
        raw_model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=NUM_CLASSES)
        try:
            state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
            raw_model.load_state_dict(state_dict)
            raw_model.eval()
            _model_wrapper = GradCAMModel(raw_model)
            print("Model and Grad-CAM wrapper loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
    return _model_wrapper

# --- 6. PREDICTION FUNCTION ---
def predict_image(image_file):
    wrapper = load_model()
    img = Image.open(image_file).convert('RGB')
    input_tensor = val_transform(img).unsqueeze(0).to(DEVICE)
    
    # Inference (No grad here because Grad-CAM needs gradients later)
    outputs = wrapper.model(input_tensor)
    probabilities = torch.nn.functional.softmax(outputs[0], dim=0).tolist()
    
    # Sensitivity Penalty (As requested)
    probabilities[0] = probabilities[0] * 0.70 
    max_prob = max(probabilities)
    predicted_class_idx = probabilities.index(max_prob)
    
    # Normalize
    total_prob = sum(probabilities)
    normalized_probs = [p / total_prob for p in probabilities]
    
    # Generate Heatmap
    heatmap = wrapper.generate_heatmap(input_tensor, predicted_class_idx)
    
    # Save Heatmap Overlay
    img_cv = cv2.cvtColor(np.array(img.resize((IMG_SIZE, IMG_SIZE))), cv2.COLOR_RGB2BGR)
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_cv, 0.6, heatmap_colored, 0.4, 0)
    
    heatmap_filename = f"heatmap_{os.path.basename(image_file.name)}"
    heatmap_path = os.path.join(settings.MEDIA_ROOT, 'heatmaps', heatmap_filename)
    os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
    cv2.imwrite(heatmap_path, overlay)

    class_mapping = {0: 'Normal', 1: 'Glaucoma', 2: 'Diabetic Retinopathy', 3: 'Cataract', 4: 'AMD'}
    
    return {
        'diagnosis': class_mapping[predicted_class_idx],
        'confidence': f"{normalized_probs[predicted_class_idx] * 100:.2f}%",
        'heatmap_url': os.path.join(settings.MEDIA_URL, 'heatmaps', heatmap_filename),
        'all_probs': {k: f"{v*100:.1f}%" for k, v in zip(class_mapping.values(), normalized_probs)}
    }