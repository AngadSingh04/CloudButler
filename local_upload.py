#Local Backend code for uploading file to S3

import os
import time
import boto3
from decimal import Decimal  
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timedelta, timezone

# Configuration
LOCAL_FOLDER = '/Users/angadsingh04/Desktop/TestR' 
AWS_REGION = 'us-east-1'  
POLL_INTERVAL = 10  

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
s3 = boto3.client('s3', region_name=AWS_REGION)
upload_requests_table = dynamodb.Table('VirtualAssistant-FileUploadRequest')

class UploadHandler:
    def __init__(self):
        self.processed_requests = set()
        self.processed_downloads = set()
        
    def check_for_requests(self):
        try:
            # Get requests from the last hour that are pending
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            response = upload_requests_table.scan(
                FilterExpression='#st = :status AND #ts > :time',
                ExpressionAttributeNames={
                    '#st': 'status',
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':status': 'pending',
                    ':time': one_hour_ago
                }
            )
            
            for item in response.get('Items', []):
                request_id = item['request_id']
                if request_id not in self.processed_requests:
                    self.process_upload_request(item)
                    self.processed_requests.add(request_id)
                    
        except Exception as e:
            print(f"Error checking for requests: {e}")
    
    def process_upload_request(self, request):
        file_name = request['file_name']
        bucket_name = request['bucket_name']
        request_id = request['request_id']
        
        local_path = os.path.join(LOCAL_FOLDER, file_name)
        
        if not os.path.exists(local_path):
            print(f"File not found: {local_path}")
            self.update_request_status(request, 'failed', 'File not found')
            return
        
        try:
            s3.upload_file(local_path, bucket_name, file_name)
            print(f"Successfully uploaded {file_name} to {bucket_name}")
            self.update_request_status(request, 'completed')
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            self.update_request_status(request, 'failed', str(e))
    
    def update_request_status(self, request, status, error_message=None):
        try:
            update_values = {
                ':status': status,
                ':updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            update_expression = 'SET #st = :status, #ua = :updated_at'
            
            if error_message:
                update_values[':error'] = error_message
                update_expression += ', error_message = :error'
            
            
            key = {
                'request_id': request['request_id'],
                'timestamp': request['timestamp']
            }
            
            print(f"Using key for update: {key}")
            
            upload_requests_table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames={
                    '#st': 'status',
                    '#ua': 'updated_at'
                },
                ExpressionAttributeValues=update_values
            )
            print(f"Successfully updated request status to: {status}")
            
        except Exception as e:
            print(f"Error updating request status: {e}")
            print(f"Request item keys: {list(request.keys())}")
            print(f"Request item: {request}")
            
            if 'request_id' not in request:
                print("ERROR: request_id missing from request item!")
            if 'timestamp' not in request:
                print("ERROR: timestamp missing from request item!")
    
    def check_for_download_requests(self):
        """Check for download requests from Alexa"""
        try:
            
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            download_requests_table = dynamodb.Table('VirtualAssistant-FileDownloadRequest')
            response = download_requests_table.scan(
                FilterExpression='#st = :status AND #ts > :time',
                ExpressionAttributeNames={
                    '#st': 'status',
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':status': 'pending',
                    ':time': one_hour_ago
                }
            )
            
            for item in response.get('Items', []):
                request_id = item['request_id']
                if request_id not in self.processed_downloads:
                    self.process_download_request(item)
                    self.processed_downloads.add(request_id)
                    
        except Exception as e:
            print(f"Error checking for download requests: {e}")
            
    def process_download_request(self, request):
        """Process a download request from S3 to local folder"""
        file_name = request['file_name']
        bucket_name = request['bucket_name']
        request_id = request['request_id']
        
        local_path = os.path.join(LOCAL_FOLDER, file_name)
        
        
        if os.path.exists(local_path):
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_name}_{timestamp}_backup"
            backup_path = os.path.join(LOCAL_FOLDER, backup_name)
            os.rename(local_path, backup_path)
            print(f"Existing file backed up as: {backup_name}")
        
        try:
           
            s3.download_file(bucket_name, file_name, local_path)
            print(f"Successfully downloaded {file_name} from {bucket_name} to {local_path}")
            self.update_download_request_status(request, 'completed')
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            self.update_download_request_status(request, 'failed', str(e))
            
    def update_download_request_status(self, request, status, error_message=None):
        """Update download request status in DynamoDB"""
        try:
            download_requests_table = dynamodb.Table('VirtualAssistant-FileDownloadRequest')
            
            update_values = {
                ':status': status,
                ':updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            update_expression = 'SET #st = :status, #ua = :updated_at'
            
            if error_message:
                update_values[':error'] = error_message
                update_expression += ', error_message = :error'
            
            key = {
                'request_id': request['request_id'],
                'timestamp': request['timestamp']
            }
            
            download_requests_table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames={
                    '#st': 'status',
                    '#ua': 'updated_at'
                },
                ExpressionAttributeValues=update_values
            )
            print(f"Successfully updated download request status to: {status}")
            
        except Exception as e:
            print(f"Error updating download request status: {e}")
            
    def monitor_cost_metrics(self):
        """Monitor and log S3 cost metrics"""
        try:
            
            response = s3.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                try:
                    
                    paginator = s3.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=bucket_name)
                    
                    total_size = 0
                    object_count = 0
                    storage_classes = {}
                    
                    for page in pages:
                        for obj in page.get('Contents', []):
                            object_count += 1
                            total_size += obj['Size']
                            
                            
                            storage_class = obj.get('StorageClass', 'STANDARD')
                            storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1
                    
                    
                    total_size_decimal = Decimal(str(total_size))
                    size_gb_decimal = Decimal(str(round(total_size / (1024**3), 3)))
                    
                    
                    cost_metrics_table = dynamodb.Table('VirtualAssistant-CostMetrics')
                    cost_metrics_table.put_item(
                        Item={
                            'bucket_name': bucket_name,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'total_size_bytes': total_size_decimal,  
                            'object_count': object_count,  
                            'storage_classes': storage_classes,
                            'size_gb': size_gb_decimal  
                        }
                    )
                    
                    print(f"Logged metrics for {bucket_name}: {object_count} objects, {total_size/(1024**2):.2f} MB")
                    
                except Exception as bucket_error:
                    print(f"Error monitoring bucket {bucket_name}: {bucket_error}")
                    
        except Exception as e:
            print(f"Error monitoring cost metrics: {e}")
            

class FolderMonitor(FileSystemEventHandler):
    def __init__(self, upload_handler):
        self.upload_handler = upload_handler
    
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            self.upload_handler.check_for_requests()

def main():
    upload_handler = UploadHandler()
    
    # Set up folder monitoring
    event_handler = FolderMonitor(upload_handler)
    observer = Observer()
    observer.schedule(event_handler, LOCAL_FOLDER, recursive=False)
    observer.start()
    
    print(f"Monitoring {LOCAL_FOLDER} for new files...")
    print("Also checking for download requests and monitoring costs...")
    print("Press Ctrl+C to stop")
    
    try:
        loop_counter = 0
        while True:
            
            upload_handler.check_for_requests()
            
              
            upload_handler.check_for_download_requests()
            
            
            if loop_counter % 60 == 0:
                upload_handler.monitor_cost_metrics()
            
            loop_counter += 1
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
