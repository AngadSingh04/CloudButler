# CloudButler

# 🗣️ Alexa S3 Manager

[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Lambda%20%7C%20DynamoDB-orange?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/)
[![Alexa](https://img.shields.io/badge/Alexa-Skills%20Kit-00CAFF?style=flat-square&logo=amazon-alexa)](https://developer.amazon.com/alexa)
[![Node.js](https://img.shields.io/badge/Node.js-Backend-green?style=flat-square&logo=node.js)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

**An intelligent voice-controlled S3 bucket management system that combines Alexa Skills, AWS Lambda, and a local backend for seamless file operations and cost optimization.**

---

## 🎯 **What is Alexa S3 Manager?**

Alexa S3 Manager is a comprehensive cloud storage solution that lets you manage your AWS S3 buckets and files using just your voice. With integrated cost optimization, real-time monitoring, and analytics, it transforms how you interact with cloud storage.

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Alexa Device   │───▶│  Alexa Skills    │───▶│   AWS Lambda    │
│                 │    │     Kit          │    │   Functions     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│ Local Backend   │◀───│  File Monitoring │    │   Amazon S3     │
│   (Node.js)     │    │     System       │    │   Buckets       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                                              │
        ▼                                              ▼
┌─────────────────┐                            ┌─────────────────┐
│                 │                            │                 │
│ Local Folder    │                            │   DynamoDB      │
│  Monitoring     │                            │  (Metadata)     │
└─────────────────┘                            └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │                 │
                                               │   Analytics     │
                                               │   Dashboard     │
                                               └─────────────────┘
```

**🔗 [View Detailed Architecture Diagram](https://your-architecture-diagram-link.com)**

---

## ✨ **Key Features**

### 🗣️ **Voice Commands**
- **"Alexa, create S3 bucket [bucket-name]"** - Creates new S3 buckets instantly
- **"Alexa, put [filename] into [bucket-name]"** - Upload files to specified buckets
- **"Alexa, suggest cost optimization for [bucket-name]"** - Get intelligent cost recommendations
- **"Alexa, optimize files in [bucket-name]"** - Apply lifecycle policies automatically
- **"Alexa, download [filename] from [bucket-name]"** - Download files to local folder

### 💰 **Cost Optimization Engine**
- Intelligent analysis of file access patterns
- Automatic lifecycle policy recommendations
- Storage class optimization (Standard → IA → Glacier)
- Cost savings reports and projections

### 📊 **Real-time Monitoring**
- Local folder monitoring with instant file detection
- Automatic file metadata extraction
- Real-time sync between local and cloud storage

### 📈 **Analytics Dashboard**
- Intent call history and analytics
- Total bucket and file statistics
- Cost optimization tracking
- Usage patterns and trends

---

## 🚀 **Quick Start**

### Prerequisites
- AWS Account with appropriate permissions
- Amazon Developer Account (for Alexa Skills)
- Node.js 16+ installed locally
- AWS CLI configured

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/alexa-s3-manager.git
cd alexa-s3-manager
```

### 2. Install Dependencies
```bash
# Install local backend dependencies
npm install

# Install Lambda function dependencies
cd lambda-functions
npm install
```

### 3. Configure AWS Services
```bash
# Deploy Lambda functions
aws lambda create-function --function-name alexa-s3-manager \
  --runtime nodejs18.x --role arn:aws:iam::account:role/lambda-role \
  --handler index.handler --zip-file fileb://function.zip

# Create DynamoDB table
aws dynamodb create-table --table-name AlexaS3Manager \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 4. Set Up Alexa Skill
1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Create a new skill with the provided interaction model
3. Configure the endpoint to point to your Lambda function
4. Test your skill in the simulator

### 5. Start Local Backend
```bash
# Set environment variables
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=AlexaS3Manager
export MONITOR_FOLDER=/path/to/your/folder

# Start the backend
npm start
```

---

## 🎮 **Usage Examples**

### Creating and Managing Buckets
```
You: "Alexa, open S3 Manager"
Alexa: "Welcome to S3 Manager. What would you like to do?"

You: "Create S3 bucket my-project-bucket"
Alexa: "I've successfully created the bucket 'my-project-bucket' for you."
```

### File Operations
```
You: "Put document.pdf into my-project-bucket"
Alexa: "I've uploaded document.pdf to my-project-bucket successfully."

You: "Download report.xlsx from my-project-bucket"
Alexa: "I'm downloading report.xlsx to your local folder now."
```

### Cost Optimization
```
You: "Suggest cost optimization for my-project-bucket"
Alexa: "I found 15 files that haven't been accessed in 30 days. You could save $23.50 monthly by moving them to Infrequent Access storage."

You: "Optimize files in my-project-bucket"
Alexa: "I've applied lifecycle policies to optimize your storage costs."
```

---

## 🛠️ **Technical Architecture**

### Components

#### 🔧 **Alexa Skill**
- **Intent Recognition**: Natural language processing for voice commands
- **Session Management**: Maintains context across conversations
- **Error Handling**: Graceful failure recovery and user feedback

#### ⚡ **AWS Lambda Functions**
- **S3 Operations**: Bucket creation, file upload/download, listing
- **Cost Analysis**: Storage pattern analysis and optimization recommendations
- **DynamoDB Integration**: Metadata storage and retrieval

#### 🖥️ **Local Backend (Node.js)**
- **File Monitoring**: Real-time folder watching using `chokidar`
- **AWS SDK Integration**: Direct S3 and DynamoDB operations
- **REST API**: Endpoints for dashboard and external integrations

#### 🗄️ **Data Storage**
- **Amazon S3**: Primary file storage with intelligent tiering
- **DynamoDB**: Metadata, analytics, and configuration storage
- **Local Storage**: Temporary file staging and downloads

---

## 📊 **Analytics & Monitoring**

### Dashboard Metrics
- **Total Buckets**: Real-time count of managed S3 buckets
- **File Statistics**: Number of files, total storage used, cost breakdown
- **Intent History**: Chronological log of all Alexa interactions
- **Cost Savings**: Tracked savings from optimization recommendations

### Supported Analytics
- Daily/Weekly/Monthly usage patterns
- Most accessed files and buckets
- Cost optimization impact reports
- Voice command success rates

---


<div align="center">

**⭐ If this project helped you, please give it a star! ⭐**

Made with ❤️ and lots of ☕

</div>
