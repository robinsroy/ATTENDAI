# face_utils.py
"""
Face Recognition Utilities using DeepFace
- Face Detection using OpenCV/RetinaFace
- Face Embedding using VGG-Face/Facenet
- Face Matching using Cosine Similarity
"""

import numpy as np
import os
import cv2
from deepface import DeepFace
from numpy.linalg import norm

# Model configuration - using VGG-Face for embeddings
MODEL_NAME = "VGG-Face"  # Fast and accurate, can also use "Facenet", "Facenet512", "ArcFace"
DETECTOR_BACKEND = "opencv"  # Fast detector, can use "retinaface" for better accuracy

def get_embeddings_from_image_bgr(bgr_image, enforce_detection=False):
    """
    Extract face embeddings from a BGR image (OpenCV format).
    Returns list of embeddings and their face regions.
    
    Args:
        bgr_image: BGR image from OpenCV
        enforce_detection: If True, raises error when no face found. If False, returns empty list.
    
    Returns:
        embeddings: List of face embedding vectors (numpy arrays)
        faces: List of face detection information (coordinates, etc.)
    """
    try:
        # Convert BGR to RGB (DeepFace expects RGB)
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        
        # Extract embeddings using DeepFace
        # This will detect faces and generate embeddings
        result = DeepFace.represent(
            img_path=rgb_image,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=enforce_detection
        )
        
        embeddings = []
        faces = []
        
        # DeepFace returns a list of dictionaries (one per face)
        for face_data in result:
            # Get embedding vector
            embedding = np.array(face_data['embedding'], dtype=np.float32)
            
            # Normalize embedding (L2 normalization)
            embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            embeddings.append(embedding)
            
            # Get face region if available
            face_info = {
                'facial_area': face_data.get('facial_area', {}),
                'embedding': embedding
            }
            faces.append(face_info)
        
        return embeddings, faces
    
    except Exception as e:
        print(f"Face detection error: {str(e)}")
        return [], []

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (norm(a) * norm(b) + 1e-10)

def match_embedding_to_db(query_emb, enrolled_dict, threshold=0.40):
    """
    Match a query embedding against enrolled student embeddings.
    
    Args:
        query_emb: Query face embedding (numpy array, 1D)
        enrolled_dict: Dictionary of {student_id: embeddings_array (2D numpy array)}
        threshold: Minimum similarity score (0.35-0.45 recommended for VGG-Face)
    
    Returns:
        best_student_id: ID of matched student (or None)
        best_score: Similarity score
    """
    best_id = None
    best_score = -1.0
    
    # Ensure query is 1D
    if len(query_emb.shape) > 1:
        query_emb = query_emb.flatten()
    
    for student_id, embeddings in enrolled_dict.items():
        # embeddings is a 2D array: shape (num_samples, embedding_dim)
        # We need to compare query against each sample
        if len(embeddings.shape) == 1:
            # Single embedding, reshape to 2D
            embeddings = embeddings.reshape(1, -1)
        
        for enrolled_emb in embeddings:
            # Calculate cosine similarity
            score = float(cosine_similarity(query_emb, enrolled_emb))
            
            if score > best_score:
                best_score = score
                best_id = student_id
    
    if best_score >= threshold:
        return best_id, best_score
    
    return None, best_score

def load_all_enrollments(encodings_folder='encodings'):
    """
    Load all student face embeddings from the encodings folder.
    
    Returns:
        enrolled: Dictionary of {student_id: numpy_array_of_embeddings}
    """
    enrolled = {}
    
    if not os.path.exists(encodings_folder):
        os.makedirs(encodings_folder)
        return enrolled
    
    for filename in os.listdir(encodings_folder):
        if filename.endswith('.npy'):
            student_id = os.path.splitext(filename)[0]
            filepath = os.path.join(encodings_folder, filename)
            
            try:
                # Load embeddings array
                embeddings = np.load(filepath)
                
                # Ensure normalized
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
                embeddings = embeddings / norms
                
                enrolled[student_id] = embeddings
                print(f"✅ Loaded {len(embeddings)} embeddings for student {student_id}")
            except Exception as e:
                print(f"❌ Error loading embeddings for {student_id}: {str(e)}")
    
    return enrolled

def append_embedding_for_student(student_id, new_emb, encodings_folder='encodings'):
    """
    Add a new face embedding for a student.
    
    Args:
        student_id: Student ID
        new_emb: New embedding vector (numpy array)
        encodings_folder: Folder to store embeddings
    """
    if not os.path.exists(encodings_folder):
        os.makedirs(encodings_folder)
    
    filepath = os.path.join(encodings_folder, f"{student_id}.npy")
    
    # Ensure embedding is 2D array
    if len(new_emb.shape) == 1:
        new_emb = new_emb.reshape(1, -1)
    
    if os.path.exists(filepath):
        # Append to existing embeddings
        existing_embs = np.load(filepath)
        updated_embs = np.vstack([existing_embs, new_emb])
    else:
        # Create new file
        updated_embs = new_emb
    
    np.save(filepath, updated_embs)
    print(f"✅ Saved embedding for student {student_id} ({len(updated_embs)} total)")

def detect_faces_in_image(bgr_image):
    """
    Detect faces in an image and return bounding boxes.
    Used for visualization/testing purposes.
    
    Returns:
        faces: List of face regions with coordinates
    """
    try:
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        
        result = DeepFace.extract_faces(
            img_path=rgb_image,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False
        )
        
        faces = []
        for face_data in result:
            facial_area = face_data.get('facial_area', {})
            faces.append({
                'x': facial_area.get('x', 0),
                'y': facial_area.get('y', 0),
                'w': facial_area.get('w', 0),
                'h': facial_area.get('h', 0),
                'confidence': face_data.get('confidence', 0)
            })
        
        return faces
    except Exception as e:
        print(f"Face detection error: {str(e)}")
        return []

# Test function
def test_face_detection():
    """Test if face detection is working"""
    print("=" * 50)
    print("🧪 Testing DeepFace Face Recognition System")
    print("=" * 50)
    print(f"📌 Model: {MODEL_NAME}")
    print(f"📌 Detector: {DETECTOR_BACKEND}")
    print("=" * 50)
    
    try:
        # Test with a simple image
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = DeepFace.represent(
            img_path=test_img,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False
        )
        print("✅ DeepFace is working correctly!")
        print("✅ Face recognition system is ready!")
        return True
    except Exception as e:
        print(f"❌ DeepFace test failed: {str(e)}")
        return False

if __name__ == '__main__':
    test_face_detection()
