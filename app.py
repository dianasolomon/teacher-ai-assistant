from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from extractor import extract_text
from chunker import chunk_text
from embedder import generate_embeddings
from vector_store import save_to_vector_store

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/upload", methods=['POST'])
def upload_file():
    """
    Upload endpoint for teacher notes (PDF and .txt files only)
    """
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and .txt files are allowed"}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Print success message to console
    print(f"✅ FILE UPLOADED SUCCESSFULLY: {filename}")
    print(f"   Saved to: {filepath}")
    
    # Extract text from uploaded file
    try:
        extracted_text = extract_text(filepath)
        text_length = len(extracted_text)
        
        # Chunk the extracted text
        chunks = chunk_text(extracted_text)
        
        # Generate embeddings for chunks
        embedding_pairs = generate_embeddings(chunks)
        
        # Save embeddings to FAISS vector store
        save_to_vector_store(embedding_pairs, filename)
        
        # Extract just the embeddings and chunks for response
        embedding_dim = embedding_pairs[0][0].shape[0] if embedding_pairs else 0
        
        return jsonify({
            "message": "✅ PHASE 1 COMPLETE - File uploaded, processed, and saved to vector store!",
            "filename": filename,
            "filepath": filepath,
            "text_length": text_length,
            "total_chunks": len(chunks),
            "total_embeddings": len(embedding_pairs),
            "embedding_dimension": embedding_dim,
            "vector_store_saved": True,
            "chunk_preview": chunks[0][:150] if chunks else ""
        }), 200
    
    except Exception as e:
        print(f"❌ ERROR PROCESSING FILE: {str(e)}")
        return jsonify({
            "error": f"File uploaded but processing failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
