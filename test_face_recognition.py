"""
Test script to verify face recognition setup
"""
import sys
sys.path.insert(0, r'c:\projects\Attendai')

print("=" * 60)
print("Testing Face Recognition Setup")
print("=" * 60)

# Test 1: Check encodings file exists
print("\n1. Checking encodings file...")
import os
encodings_path = r'c:\projects\Attendai\encodings\5.npy'
if os.path.exists(encodings_path):
    size = os.path.getsize(encodings_path)
    print(f"   ✅ Encodings file exists: {encodings_path}")
    print(f"   📦 Size: {size} bytes")
else:
    print(f"   ❌ Encodings file NOT found: {encodings_path}")

# Test 2: Load encodings
print("\n2. Loading face encodings...")
try:
    from face_utils import load_all_enrollments
    enrolled = load_all_enrollments()
    print(f"   ✅ Loaded {len(enrolled)} enrolled students")
    for student_id, embedding in enrolled.items():
        print(f"   - Student ID {student_id}: embedding shape = {embedding.shape}")
except Exception as e:
    print(f"   ❌ Error loading enrollments: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test face detection on sample image
print("\n3. Testing face detection...")
try:
    import cv2
    import numpy as np
    from face_utils import get_embeddings_from_image_bgr
    
    # Load a sample image
    sample_path = r'c:\projects\Attendai\dataset\S03\sample_0.jpg'
    if os.path.exists(sample_path):
        img = cv2.imread(sample_path)
        print(f"   ✅ Loaded sample image: {img.shape}")
        
        print("   🧠 Extracting embeddings...")
        embeddings_list, faces = get_embeddings_from_image_bgr(img)
        
        if embeddings_list and len(embeddings_list) > 0:
            embedding = embeddings_list[0]
            print(f"   ✅ Embeddings extracted: shape = {embedding.shape}")
            print(f"   📊 Number of faces detected: {len(embeddings_list)}")
        else:
            embedding = None
            print("   ❌ No face detected in sample image")
    else:
        print(f"   ⚠️ Sample image not found: {sample_path}")
        
except Exception as e:
    print(f"   ❌ Error testing face detection: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test matching
print("\n4. Testing face matching...")
try:
    if 'enrolled' in locals() and 'embedding' in locals() and embedding is not None:
        from face_utils import match_embedding_to_db
        
        matched_id, confidence = match_embedding_to_db(embedding, enrolled, threshold=0.40)
        
        if matched_id:
            print(f"   ✅ Match found!")
            print(f"   - Student ID: {matched_id}")
            print(f"   - Confidence: {confidence:.4f}")
        else:
            print("   ❌ No match found")
    else:
        print("   ⏭️ Skipping - prerequisites not met")
        
except Exception as e:
    print(f"   ❌ Error testing matching: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
