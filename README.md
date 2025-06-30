# CloudButler

# 🗣️ Alexa S3 Manager

[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Lambda%20%7C%20DynamoDB-orange?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/)
[![Alexa](https://img.shields.io/badge/Alexa-Skills%20Kit-00CAFF?style=flat-square&logo=amazon-alexa)](https://developer.amazon.com/alexa)
[![Node.js](https://img.shields.io/badge/Node.js-Backend-green?style=flat-square&logo=node.js)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-Lambda-blue?style=flat-square&logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

**An intelligent voice-controlled S3 bucket management system that combines Alexa Skills, AWS Lambda, and a local backend for seamless file operations and cost optimization.**

---

## 🎯 **What is CloudButler?**

CloudButler is a comprehensive cloud storage solution that lets you manage your AWS S3 buckets and files using just your voice. With integrated cost optimization, real-time monitoring, and analytics, it transforms how you interact with cloud storage.

## 🏗️ **System Architecture**

```
![Architecture Image](./images/architecture.png)
```

---

## ✨ **Key Features**

### 🗣️ **Voice Commands**
- **"Alexa, create S3 bucket [bucket-name]"** - Creates new S3 buckets instantly
- **"Alexa, list my S3 buckets"** - Shows all your S3 buckets
- **"Alexa, upload [filename] to [bucket-name]"** - Upload files to specified buckets
- **"Alexa, download [filename] from [bucket-name]"** - Download files to local folder
- **"Alexa, suggest cost optimization for [bucket-name]"** - Get intelligent cost recommendations
- **"Alexa, optimize files in [bucket-name]"** - Apply lifecycle policies automatically

### 💰 **Cost Optimization Engine**
- Intelligent analysis of file access patterns
- Automatic lifecycle policy recommendations
- Storage class optimization (Standard → IA → Glacier → Deep Archive)
- Cost savings reports and projections

### 📊 **Real-time Analytics Dashboard**
- Intent call history and analytics
- Total bucket and file statistics
- Cost optimization tracking
- Usage patterns and trends
- Live monitoring of Alexa interactions

### 🔄 **Local File Management**
- Local folder monitoring with instant file detection
- Automatic file sync between local and cloud storage
- Queue-based upload/download system

---

## 🚀 **Quick Start**

### Prerequisites
- AWS Account with appropriate permissions
- Amazon Developer Account (for Alexa Skills)
- Python 3.8+ installed locally
- AWS CLI configured

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/cloudbutler.git
cd cloudbutler
```

### 2. Set Up AWS Lambda Function

#### Create Lambda Function
1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `cloudbutler-alexa-handler`
5. Runtime: **Python 3.9** or **Python 3.11**
6. Create function

#### Deploy Lambda Code
1. Copy the code from `lambda_function.py` in this repository
2. Paste it into the Lambda function code editor
3. Deploy the function

#### Configure Lambda Permissions
Add these permissions to your Lambda execution role:
- `AmazonS3FullAccess`
- `AmazonDynamoDBFullAccess`
- `CloudWatchLogsFullAccess`

#### Set Environment Variables (Optional)
```bash
AWS_REGION=us-east-1
```

### 3. Create DynamoDB Tables

Create the following tables in DynamoDB:

```bash
# User Profiles Table
aws dynamodb create-table \
    --table-name VirtualAssistant-UserProfiles \
    --attribute-definitions AttributeName=user_id,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Conversation History Table
aws dynamodb create-table \
    --table-name VirtualAssistant-ConversationHistory \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# Usage Analytics Table
aws dynamodb create-table \
    --table-name VirtualAssistant-UsageAnalytics \
    --attribute-definitions AttributeName=metric_type,AttributeType=S AttributeName=date,AttributeType=S \
    --key-schema AttributeName=metric_type,KeyType=HASH AttributeName=date,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# File Upload Request Table
aws dynamodb create-table \
    --table-name VirtualAssistant-FileUploadRequest \
    --attribute-definitions AttributeName=request_id,AttributeType=S \
    --key-schema AttributeName=request_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# File Download Request Table
aws dynamodb create-table \
    --table-name VirtualAssistant-FileDownloadRequest \
    --attribute-definitions AttributeName=request_id,AttributeType=S \
    --key-schema AttributeName=request_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

### 4. Set Up Alexa Skill

#### Create Alexa Skill
1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Click "Create Skill"
3. Skill name: "CloudButler" 
4. Choose "Custom" model
5. Choose "Alexa-Hosted (Python)" or "Provision your own"

#### Configure Intents
Create the following intents with their sample utterances:

**GetStatsIntent**
- "what are my stats"
- "show me my statistics"
- "tell me my usage"

**CreateSBucketIntent**
- "create S3 bucket {bucketName}"
- "make a bucket called {bucketName}"
- "create bucket {bucketName}"

**ListSBucketsIntent**
- "list my S3 buckets"
- "show me my buckets"
- "what buckets do I have"

**UploadFiletoSIntent**
- "upload {fileName} to {bucketName}"
- "put {fileName} in {bucketName}"
- "upload {fileName} to bucket {bucketName}"

**GetCostOptimizationIntent**
- "suggest cost optimization for {bucketName}"
- "analyze {bucketName} for cost savings"
- "optimize costs for {bucketName}"

**DownloadFileFromSIntent**
- "download {fileName} from {bucketName}"
- "get {fileName} from {bucketName}"
- "download {fileName} from bucket {bucketName}"

**SetupLifecyclePolicyIntent**
- "setup lifecycle policy for {bucketName}"
- "optimize {bucketName}"
- "apply lifecycle rules to {bucketName}"

#### Configure Slot Types
- **bucketName**: Custom slot type for S3 bucket names
- **fileName**: Custom slot type for file names

#### Set Endpoint
- Choose "AWS Lambda ARN"
- Paste your Lambda function ARN
- Save and build the model

### 5. Set Up Local Backend

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv cloudbutler-env

# Activate virtual environment
# On Windows:
cloudbutler-env\Scripts\activate
# On macOS/Linux:
source cloudbutler-env/bin/activate

# Install dependencies
pip install boto3 watchdog flask flask-cors python-dotenv
```

#### Configure Environment Variables
Create a `.env` file in the root directory:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
MONITOR_FOLDER=./monitored_files
DOWNLOAD_FOLDER=./downloads
```

#### Run Local Backend
```bash
python local_backend.py
```

This will start monitoring your local folder and process upload/download requests from Alexa.

### 6. Set Up Analytics Dashboard

#### Run Dashboard Backend
```bash
python dashboard_backend.py
```

This starts the Flask server for the analytics dashboard.

#### Launch Web Dashboard
1. Open `index.html` in your code editor
2. Use "Go Live" extension (or similar) to serve the HTML file
3. Navigate to the local server URL (usually `http://127.0.0.1:5500`)

The dashboard will show:
- Real-time Alexa intent analytics
- S3 bucket statistics
- File upload/download history
- Cost optimization insights

---

## 🎮 **Usage Examples**

### Creating and Managing Buckets
```
You: "Alexa, open CloudButler"
Alexa: "Welcome to CloudButler. What would you like to do?"

You: "Create S3 bucket my-project-bucket"
Alexa: "I've successfully created the bucket 'my-project-bucket' for you."

You: "List my S3 buckets"
Alexa: "You have 3 S3 buckets: my-project-bucket, demo-bucket, and backup-bucket."
```

### File Operations
```
You: "Upload document dot pdf to my-project-bucket"
Alexa: "I've queued your request to upload document.pdf to my-project-bucket. Your local agent will process this shortly."

You: "Download report dot xlsx from my-project-bucket"
Alexa: "I've queued your request to download report.xlsx from my-project-bucket to your local folder."
```

### Cost Optimization
```
You: "Suggest cost optimization for my-project-bucket"
Alexa: "Cost analysis for my-project-bucket: 150 objects (2.3 GB). Suggestions: Move 45 old files to S3 Infrequent Access; Archive 12 large files to Glacier."

You: "Setup lifecycle policy for my-project-bucket"
Alexa: "Great! I've set up a lifecycle policy for my-project-bucket. Files will automatically move to cheaper storage after 30, 90, and 365 days."
```

---

## 🛠️ **How AWS Lambda Works in This Project**

### Lambda Function Architecture

The AWS Lambda function (`lambda_function.py`) serves as the core brain of CloudButler, handling all Alexa voice interactions and AWS service integrations.

#### Key Components:

**1. Intent Handlers**
- Each Alexa intent (voice command) has a dedicated handler class
- Handlers process voice input, extract parameters, and execute AWS operations
- Example: `CreateS3BucketIntentHandler` creates S3 buckets when you say "create bucket"

**2. DynamoDB Integration**
- **User Profiles**: Stores user preferences and personalization data
- **Conversation History**: Logs all interactions for analytics
- **File Operation Queues**: Manages upload/download requests
- **Usage Analytics**: Tracks intent usage patterns

**3. S3 Operations**
- Direct S3 API calls for bucket creation, listing, and management
- Cost analysis by examining object metadata and access patterns
- Lifecycle policy management for automated cost optimization

**4. Queue-Based File Operations**
- Upload/download requests are queued in DynamoDB
- Local backend polls these queues and processes file operations
- Ensures reliable file handling even with network issues

#### Lambda Execution Flow:
1. **Alexa Voice Input** → Alexa Skills Kit
2. **Intent Recognition** → Lambda function triggered
3. **Parameter Extraction** → Parse voice input for file names, bucket names
4. **AWS Service Calls** → Interact with S3, DynamoDB
5. **Response Generation** → Send formatted response back to Alexa
6. **Analytics Logging** → Record interaction for dashboard

#### Why Lambda?
- **Serverless**: No server management required
- **Auto-scaling**: Handles multiple concurrent voice requests
- **Cost-effective**: Pay only for actual usage
- **AWS Integration**: Native access to S3, DynamoDB, and other AWS services
- **Low Latency**: Fast response times for voice interactions

---

## 📊 **Dashboard Features**

The web-based analytics dashboard provides real-time insights:

- **Intent Analytics**: Most used voice commands and success rates
- **Storage Overview**: Total buckets, files, and storage usage
- **Cost Tracking**: Optimization suggestions and savings achieved
- **User Activity**: Conversation history and usage patterns
- **System Health**: Lambda function performance and error rates

---

## 🔧 **Configuration**

### Environment Variables
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Local Monitoring
MONITOR_FOLDER=./monitored_files
DOWNLOAD_FOLDER=./downloads

# Dashboard Configuration
FLASK_PORT=5000
DEBUG_MODE=True
```

### AWS IAM Permissions
Your Lambda execution role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "dynamodb:*",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## 🐛 **Troubleshooting**

### Common Issues

**1. "Alexa doesn't understand my voice commands"**
- Check if your Alexa skill is enabled in the Alexa app
- Verify the skill is linked to your AWS Lambda function
- Ensure all intents are properly configured with utterances

**2. "File uploads/downloads don't work"**
- Verify your local backend is running (`python local_backend.py`)
- Check AWS credentials in your `.env` file
- Ensure the monitored folder exists and has proper permissions

**3. "Dashboard shows no data"**
- Make sure `dashboard_backend.py` is running
- Verify DynamoDB tables exist and have data
- Check browser console for JavaScript errors

**4. "Cost optimization suggestions are inaccurate"**
- Ensure Lambda function has S3 read permissions
- Check if the bucket name in your voice command is correct
- Verify the bucket exists and is accessible

### Logs and Debugging
- **Lambda Logs**: Check CloudWatch logs for the Lambda function
- **Local Backend**: Check console output for error messages
- **Dashboard**: Use browser developer tools to debug frontend issues

---

## 🤝 **Contributing**

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- Amazon Alexa Skills Kit for voice interaction capabilities
- AWS Lambda for serverless computing
- AWS S3 for reliable cloud storage
- DynamoDB for fast, scalable database operations

---

<div align="center">

**⭐ If this project helped you, please give it a star! ⭐**

Made with ❤️ for the cloud computing community

</div>
