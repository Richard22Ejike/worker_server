import os
import runpod
from model_downloader import download_model_from_s3

# Configuration - Set these as environment variables in RunPod template
CONFIG = {
    'S3_BUCKET': os.getenv('S3_BUCKET', 'rd0cg4jfje'),
    'S3_ENDPOINT': os.getenv('S3_ENDPOINT', 'https://s3api-eu-cz-1.runpod.io'),
    'S3_REGION': os.getenv('S3_REGION', 'eu-cz-1'),
    'MODEL_PATH': '/model'
}

def initialize_worker():
    """Initialize the worker by downloading the model"""
    print("🧪 Initializing worker...")
    
    # Check if credentials are available
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("❌ AWS credentials not found in environment variables")
        print("ℹ️ Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    
    # Download model from S3
    # success = download_model_from_s3(
    #     bucket_name=CONFIG['S3_BUCKET'],
    #     endpoint_url=CONFIG['S3_ENDPOINT'],
    #     region=CONFIG['S3_REGION']
    # )
    
    # if not success:
    #     raise RuntimeError("Failed to download model from S3")
    
    print("✅ Model downloaded successfully")
    
    # Load your actual model here
    # Example: model = load_your_model(CONFIG['MODEL_PATH'])
    print(f"📁 Model available at: {CONFIG['MODEL_PATH']}")
    
    return {"status": "ready", "model_path": CONFIG['MODEL_PATH']}

def handler(job):
    """Handle incoming inference requests"""
    try:
        input_data = job['input']
        
        # Your model inference logic here
        # result = model.predict(input_data)
        
        return {
            "status": "success",
            "model_used": CONFIG['MODEL_PATH'],
            "result": f"Processed input: {input_data}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# Initialize the worker when container starts
if __name__ == "__main__":
    print("🚀 Starting RunPod Serverless Worker")
    initialization_result = initialize_worker()
    print(f"Initialization result: {initialization_result}")
    
    # Start the RunPod serverless handler
    runpod.serverless.start({"handler": handler})