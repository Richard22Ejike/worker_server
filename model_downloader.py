import os
import boto3
import time
import requests
from botocore.client import Config
from botocore.exceptions import NoCredentialsError, ClientError
from tqdm import tqdm
import json
from pathlib import Path

class ModelDownloader:
    def __init__(self, bucket_name, endpoint_url, region):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region = region
        self.s3 = self._create_s3_client()
        self.model_path = "/model"
        
    def _create_s3_client(self):
        """Create S3 client with proper configuration for RunPod"""
        try:
            # Check if we're in RunPod environment (credentials should be set via env vars)
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not access_key or not secret_key:
                print("⚠️  AWS credentials not found in environment variables")
                print("ℹ️  Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
                return None
            
            return boto3.client('s3',
                            endpoint_url=self.endpoint_url,
                            region_name=self.region,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            config=Config(
                                signature_version='s3v4',
                                retries={'max_attempts': 3},
                                max_pool_connections=50
                            ))
        except Exception as e:
            print(f"Error creating S3 client: {e}")
            raise
    
    def download_file(self, key, local_path):
        """Download a single file with progress bar"""
        try:
            # Get file size for progress bar
            head = self.s3.head_object(Bucket=self.bucket_name, Key=key)
            file_size = head['ContentLength']
            
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download with progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, 
                     desc=os.path.basename(key), ncols=80) as pbar:
                self.s3.download_file(
                    Bucket=self.bucket_name,
                    Key=key,
                    Filename=local_path,
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
                )
                
            return True
            
        except ClientError as e:
            print(f"Error downloading {key}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error downloading {key}: {e}")
            return False
    
    def list_bucket_contents(self):
        """List all files in the bucket"""
        try:
            objects = []
            continuation_token = None
            
            while True:
                if continuation_token:
                    response = self.s3.list_objects_v2(
                        Bucket=self.bucket_name,
                        ContinuationToken=continuation_token
                    )
                else:
                    response = self.s3.list_objects_v2(Bucket=self.bucket_name)
                
                if 'Contents' in response:
                    objects.extend(response['Contents'])
                
                if not response.get('IsTruncated'):
                    break
                    
                continuation_token = response.get('NextContinuationToken')
            
            return objects
            
        except ClientError as e:
            print(f"Error listing bucket contents: {e}")
            return []
    
    def download_model(self):
        """Main method to download entire model"""
        print(f"🚀 Starting model download from {self.bucket_name}")
        print(f"📁 Model will be saved to: {self.model_path}")
        
        # Create model directory
        os.makedirs(self.model_path, exist_ok=True)
        
        # List files in bucket
        print("📋 Listing files in bucket...")
        objects = self.list_bucket_contents()
        
        if not objects:
            print("❌ No files found in bucket")
            return False
        
        print(f"📊 Found {len(objects)} files to download")
        
        # Download each file
        success_count = 0
        failed_count = 0
        
        for obj in objects:
            key = obj['Key']
            local_file_path = os.path.join(self.model_path, key)
            
            # Skip if file already exists and is the same size
            if os.path.exists(local_file_path):
                local_size = os.path.getsize(local_file_path)
                if local_size == obj['Size']:
                    print(f"✅ Already exists: {key}")
                    success_count += 1
                    continue
            
            print(f"⬇️  Downloading: {key}")
            if self.download_file(key, local_file_path):
                success_count += 1
            else:
                failed_count += 1
        
        # Create a metadata file
        metadata = {
            'download_time': time.time(),
            'bucket_name': self.bucket_name,
            'endpoint_url': self.endpoint_url,
            'total_files': len(objects),
            'successful_downloads': success_count,
            'failed_downloads': failed_count
        }
        
        with open(os.path.join(self.model_path, 'download_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n🎉 Download completed!")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        
        return failed_count == 0
    
    def get_model_info(self):
        """Get information about the downloaded model"""
        metadata_file = os.path.join(self.model_path, 'download_metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None

# Utility function for easy usage
def download_model_from_s3(bucket_name, endpoint_url, region):
    """Convenience function to download model"""
    downloader = ModelDownloader(bucket_name, endpoint_url, region)
    return downloader.download_model()

if __name__ == "__main__":
    # Test the downloader
    downloader = ModelDownloader(
        bucket_name="rd0cg4jfje",
        endpoint_url="https://s3api-eu-cz-1.runpod.io",
        region="eu-cz-1"
    )
    downloader.download_model()