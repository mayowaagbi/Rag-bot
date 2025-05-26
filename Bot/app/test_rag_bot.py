
import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """Test if the API is running"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/ping")
        if response.status_code == 200:
            print("✅ API is running!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running on port 8000")
        return False

def upload_document(file_path):
    """Upload a document to the API"""
    print(f"\n📄 Uploading document: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f)}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document uploaded successfully!")
            print(f"Documents processed: {len(result.get('documents', []))}")
            return result
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None

def get_documents():
    """Get list of uploaded documents"""
    print("\n📋 Getting uploaded documents...")
    try:
        response = requests.get(f"{BASE_URL}/api/documents")
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Found {len(docs.get('documents', []))} documents")
            for doc in docs.get('documents', []):
                print(f"  - {doc['name']} (ID: {doc['id'][:8]}...)")
            return docs
        else:
            print(f"❌ Failed to get documents: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting documents: {str(e)}")
        return None

def send_chat_message(message, document_ids=None):
    """Send a chat message to the API"""
    print(f"\n💬 Sending chat message: '{message}'")
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": message,
                "id": "test-msg-1"
            }
        ],
        "documentIds": document_ids or []
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Chat response received:")
            print("🤖 Assistant: ", end="", flush=True)
            
            # Handle streaming response
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: '
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            continue
            print("\n")  # New line after response
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return False

def get_suggestions():
    """Get chat suggestions"""
    print("\n💡 Getting suggestions...")
    try:
        response = requests.get(f"{BASE_URL}/api/suggestions")
        if response.status_code == 200:
            suggestions = response.json()
            print("✅ Available suggestions:")
            for i, suggestion in enumerate(suggestions.get('suggestions', []), 1):
                print(f"  {i}. {suggestion}")
            return suggestions
        else:
            print(f"❌ Failed to get suggestions: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting suggestions: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting RAG Bot API Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ API is not responding. Please start your server first:")
        print("cd C:\\Users\\mayov\\rag-bot\\Bot\\")
        print("python -m app.main")
        return
    
    # Test 2: Get suggestions
    get_suggestions()
    
    # Test 3: Check existing documents
    docs = get_documents()
    
    # Test 4: Upload a document (you'll need to provide a file path)
    print("\n" + "="*50)
    print("📄 DOCUMENT UPLOAD TEST")
    print("To test document upload, place a text/PDF file in your project directory")
    print("and update the file path below:")
    
    # Example file paths - update these with your actual files
    test_files = [
        "test_document.txt",
        "sample.pdf",
        "README.md"
    ]
    
    uploaded_doc_ids = []
    for file_path in test_files:
        if os.path.exists(file_path):
            result = upload_document(file_path)
            if result and result.get('documents'):
                uploaded_doc_ids.extend([doc['id'] for doc in result['documents']])
            break
    else:
        print("ℹ️  No test files found. Skipping upload test.")
        print("   Create a file named 'test_document.txt' to test uploads.")
    
    # Test 5: Chat without documents
    print("\n" + "="*50)
    print("💬 CHAT TESTS")
    
    test_questions = [
        "Hello, how are you?",
        "What can you help me with?",
        "What is react",
        "What documents have been uploaded?"
    ]
    
    for question in test_questions:
        send_chat_message(question)
        time.sleep(1)  # Small delay between requests
    
    # Test 6: Chat with documents (if any were uploaded)
    if uploaded_doc_ids:
        print(f"\n📄 Testing chat with uploaded documents...")
        document_questions = [
            "What is this document about?",
            "Can you summarize the main points?",
            "What are the key findings?"
        ]
        
        for question in document_questions:
            send_chat_message(question, uploaded_doc_ids)
            time.sleep(1)
    
    print("\n" + "="*50)
    print("✅ Tests completed!")
    print("\nNext steps:")
    print("1. Check the FastAPI docs at: http://127.0.0.1:8000/docs")
    print("2. Upload your own documents through the API")
    print("3. Test with your specific use cases")

if __name__ == "__main__":
    main()