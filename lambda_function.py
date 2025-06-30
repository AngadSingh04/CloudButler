# Lambda Function Code

import logging
import time
import os
import json
import boto3
import traceback
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from botocore.exceptions import ClientError
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler,
    AbstractRequestInterceptor,
    AbstractResponseInterceptor
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
user_profiles_table = dynamodb.Table('VirtualAssistant-UserProfiles')
conversation_history_table = dynamodb.Table('VirtualAssistant-ConversationHistory')
usage_analytics_table = dynamodb.Table('VirtualAssistant-UsageAnalytics')

class DynamoDBHelper:
    @staticmethod
    def decimal_to_int(obj):
        if isinstance(obj, list):
            return [DynamoDBHelper.decimal_to_int(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: DynamoDBHelper.decimal_to_int(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        else:
            return obj

    @staticmethod
    def get_user_profile(user_id):
        try:
            response = user_profiles_table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                return DynamoDBHelper.decimal_to_int(response['Item'])
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    @staticmethod
    def save_user_profile(user_id, profile_data):
        try:
            profile_data['user_id'] = user_id
            profile_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            user_profiles_table.put_item(Item=profile_data)
            return True
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            return False

    @staticmethod
    def log_conversation(user_id, intent_name, request_type, utterance=None):
        try:
            conversation_history_table.put_item(
                Item={
                    'user_id': user_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'intent_name': intent_name,
                    'request_type': request_type,
                    'utterance': utterance or 'N/A',
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            )
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")

    @staticmethod
    def update_usage_analytics(metric_type, increment=1):
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            usage_analytics_table.update_item(
                Key={
                    'metric_type': metric_type,
                    'date': today
                },
                UpdateExpression='ADD #count :inc',
                ExpressionAttributeNames={'#count': 'count'},
                ExpressionAttributeValues={':inc': increment},
                ReturnValues='UPDATED_NEW'
            )
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

class RequestLoggerInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        request = handler_input.request_envelope.request
        user_id = handler_input.request_envelope.session.user.user_id
        
        intent_name = 'LaunchRequest'
        utterance = None
        
        if hasattr(request, 'intent') and request.intent:
            intent_name = request.intent.name
            if hasattr(handler_input.request_envelope, 'request') and hasattr(handler_input.request_envelope.request, 'intent'):
                utterance = str(request.intent)
        
        DynamoDBHelper.log_conversation(
            user_id=user_id,
            intent_name=intent_name,
            request_type=request.object_type,
            utterance=utterance
        )
        
        DynamoDBHelper.update_usage_analytics('total_requests')
        DynamoDBHelper.update_usage_analytics(f'intent_{intent_name}')

class ResponseLoggerInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        DynamoDBHelper.update_usage_analytics('successful_responses')

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        user_profile = DynamoDBHelper.get_user_profile(user_id)
        
        if user_profile and user_profile.get('name'):
            speak_output = f"Welcome back {user_profile['name']}! Your virtual assistant is ready to help. What can I do for you today?"
            reprompt_text = f"Hi {user_profile['name']}, I'm here to help. You can ask about your friends, weather, or say hello. What would you like to do?"
        else:
            speak_output = "Welcome to your virtual assistant! I can help you with greetings, weather, and manage your friends list. What would you like to do?"
            reprompt_text = "I'm here to help. You can ask about your friends, weather, or say hello. What would you like to try?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class HelloWorldIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        user_profile = DynamoDBHelper.get_user_profile(user_id)
        if not user_profile:
            user_profile = {
                'name': 'Angad',
                'friends': ['Akshat', 'Shubh', 'Sayam'],
                'preferences': {
                    'greeting_style': 'friendly'
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            DynamoDBHelper.save_user_profile(user_id, user_profile)
        
        name = user_profile.get('name', 'friend')
        speak_output = f"Hello {name}! I am your virtual assistant. I can help you with various tasks like checking weather, managing your friends list, and much more! What would you like to do next?"
        reprompt_text = "What can I help you with? You can ask about your friends, weather, or try adding a new friend."
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class FriendsNameIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("FriendsName")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        user_profile = DynamoDBHelper.get_user_profile(user_id)
        
        if user_profile and user_profile.get('friends'):
            friends_list = user_profile['friends']
            if len(friends_list) == 1:
                speak_output = f"Your friend is {friends_list[0]}. Would you like to add more friends or do something else?"
            elif len(friends_list) == 2:
                speak_output = f"Your friends are {friends_list[0]} and {friends_list[1]}. What else can I help you with?"
            else:
                friends_str = ", ".join(friends_list[:-1]) + f", and {friends_list[-1]}"
                speak_output = f"Your friends are: {friends_str}. What would you like to do next?"
        else:
            speak_output = "You haven't added any friends yet. Would you like me to help you add some friends?"
        
        reprompt_text = "What else can I help you with? You can add friends, check weather, or ask me anything else."
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class AddFriendIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        is_match = ask_utils.is_intent_name("AddFriendIntent")(handler_input)
        logger.info(f"AddFriendIntentHandler.can_handle: {is_match}")
        return is_match

    def handle(self, handler_input):
        logger.info("AddFriendIntentHandler.handle called")
        user_id = handler_input.request_envelope.session.user.user_id
        
        logger.info(f"Request: {handler_input.request_envelope.request}")
        
        try:
            slots = handler_input.request_envelope.request.intent.slots
            logger.info(f"Available slots: {list(slots.keys())}")
            
            friend_name = None
            for slot_name in ["friendName", "friend_name", "FRIEND_NAMES"]:
                if slot_name in slots and slots[slot_name].value:
                    friend_name = slots[slot_name].value.strip().title()
                    logger.info(f"Found friend name '{friend_name}' in slot '{slot_name}'")
                    break
            
            if not friend_name:
                logger.warning("No friend name found in any slot")
                
        except (AttributeError, KeyError, ValueError) as e:
            logger.error(f"Error extracting friend name: {e}")
            friend_name = None
        
        if not friend_name or not friend_name.replace(" ", "").isalpha():
            speak_output = "I didn't catch a valid friend's name. Please say something like 'add John as a friend'."
            reprompt_text = "What's the name of the friend you'd like to add?"
            return (
                handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
            )
        
        user_profile = DynamoDBHelper.get_user_profile(user_id) or {}
        user_profile.setdefault("friends", [])
        
        current_friends = user_profile["friends"]
        if any(friend.lower() == friend_name.lower() for friend in current_friends):
            speak_output = f"{friend_name} is already in your friends list! What else can I help you with?"
            reprompt_text = "What would you like to do next?"
        else:
            current_friends.append(friend_name)
            user_profile["friends"] = current_friends
            
            try:
                DynamoDBHelper.save_user_profile(user_id, user_profile)
                friend_count = len(current_friends)
                speak_output = (
                    f"Great! I've added {friend_name} to your friends list. "
                    f"You now have {friend_count} friend{'s' if friend_count != 1 else ''}. "
                    f"What else can I help you with?"
                )
                reprompt_text = "Would you like to add another friend or do something else?"
                logger.info(f"Successfully added {friend_name} to friends list")
            except Exception as e:
                logger.error(f"Error saving friend: {str(e)}")
                speak_output = "Sorry, I encountered an error saving your friend. Please try again later."
                reprompt_text = "What else can I help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class GetStatsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetStatsIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        try:
            response = conversation_history_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
            )
            
            total_conversations = response['Count']
            
            user_profile = DynamoDBHelper.get_user_profile(user_id)
            friends_count = len(user_profile.get('friends', [])) if user_profile else 0
            
            speak_output = f"Here are your stats: You've had {total_conversations} conversations with me, and you have {friends_count} friends in your list. What else would you like to know?"
            reprompt_text = "What can I help you with next?"
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            speak_output = "I'm having trouble getting your stats right now. Please try again later. What else can I help you with?"
            reprompt_text = "What would you like to do?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class WeatherIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("WeatherIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        user_profile = DynamoDBHelper.get_user_profile(user_id)
        location = "your area"
        if user_profile and user_profile.get('preferences', {}).get('location'):
            location = user_profile['preferences']['location']
        
        speak_output = f"The weather in {location} is sunny and 75 degrees. This is still a placeholder, but now it's personalized to your profile! What else can I help you with?"
        reprompt_text = "What would you like to do next?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class CreateS3BucketIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CreateSBucketIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id

        slots = handler_input.request_envelope.request.intent.slots
        bucket_name = slots.get("bucketName").value if "bucketName" in slots else None

        if not bucket_name:
            speak_output = "Please tell me the name of the bucket you want to create."
            reprompt_text = "What's the name of the bucket you'd like me to create?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt_text)
                    .response
            )

        s3 = boto3.client('s3')
        try:
            s3.create_bucket(Bucket=bucket_name)
            speak_output = f"Bucket named {bucket_name} has been created successfully. What else can I help you with?"
            reprompt_text = "What would you like to do next?"
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
            speak_output = f"Sorry, I couldn't create the bucket. Error: {str(e)}. What else can I help you with?"
            reprompt_text = "What would you like to do next?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )


class ListS3BucketsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ListSBucketsIntent")(handler_input)

    def handle(self, handler_input):
        try:
            s3 = boto3.client('s3')
            response = s3.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            
            if not buckets:
                speak_output = "You don't have any S3 buckets yet. Would you like to create one?"
                reprompt_text = "Would you like to create a new bucket?"
            else:
                if len(buckets) == 1:
                    speak_output = f"You have 1 S3 bucket named {buckets[0]}. What would you like to do next?"
                else:
                    bucket_list = ", ".join(buckets[:-1]) + f" and {buckets[-1]}" if len(buckets) > 1 else buckets[0]
                    speak_output = f"You have {len(buckets)} S3 buckets: {bucket_list}. What would you like to do next?"
                
                reprompt_text = "What can I help you with next?"
                
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            speak_output = "Sorry, I couldn't retrieve your bucket list. Please try again later."
            reprompt_text = "What else can I help you with?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )


class UploadFileToS3IntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("UploadFiletoSIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        slots = handler_input.request_envelope.request.intent.slots

        file_name = slots.get("fileName", {}).value
        bucket_name = slots.get("bucketName", {}).value

        if file_name:
            file_name = file_name.replace(" dot ", ".")
            
            parts = file_name.split()
            
            common_extensions = ['jpeg', 'jpg', 'png', 'txt', 'pdf', 'doc', 'docx', 'mp3', 'mp4', 'wav']
            
            if len(parts) >= 2:
                last_part = parts[-1].lower()
                if last_part in common_extensions:
                    base_name = " ".join(parts[:-1])
                    file_name = f"{base_name}.{last_part}"
                    
            file_name = file_name.replace(".text", ".txt")
            file_name = file_name.replace(" dot text", ".txt")
            file_name = file_name.replace(" text", ".txt")
            
            file_name = file_name.replace(" ", "_")
            
            if not "." in file_name:
                parts = file_name.split("_")
                if len(parts) >= 2:
                    last_part = parts[-1].lower()
                    extension_mappings = {
                        'text': 'txt',
                        'txt': 'txt',
                        'jpeg': 'jpeg',
                        'jpg': 'jpg',
                        'png': 'png',
                        'pdf': 'pdf',
                        'doc': 'doc',
                        'document': 'doc'
                    }
                    
                    if last_part in extension_mappings:
                        base_name = "_".join(parts[:-1])
                        extension = extension_mappings[last_part]
                        file_name = f"{base_name}.{extension}"

        if not file_name or not bucket_name:
            speak_output = "Please specify both a file name and a bucket name. For example, 'Upload hello txt to angadangad' or 'Upload angad dot jpeg to demoS3bucket'."
            reprompt_text = "What file would you like to upload and to which bucket?"
            return (
                handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
            )

        request_id = f"{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            logger.info(f"Preparing to write to DynamoDB: file={file_name}, bucket={bucket_name}, user_id={user_id}, request_id={request_id}")
            upload_table = dynamodb.Table('VirtualAssistant-FileUploadRequest')
            upload_table.put_item(
                Item={
                    'request_id': request_id,
                    'user_id': user_id,
                    'file_name': file_name,
                    'bucket_name': bucket_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': 'pending',
                    'expiration_time': int(time.time()) + 3600
                }
            )

            speak_output = f"I've queued your request to upload {file_name} to {bucket_name}. Your local agent will process this shortly."
            reprompt_text = "What else can I help you with?"

        except Exception as e:
            logger.error(f"❌ Exception in UploadFileToS3IntentHandler: {e}")
            traceback.print_exc()
            speak_output = "Sorry, I couldn't process your upload request. Please try again later."
            reprompt_text = "What else can I help you with?"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(reprompt_text)
            .response
        )
class GetCostOptimizationSuggestionsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetCostOptimizationIntent")(handler_input)

    def handle(self, handler_input):
        logger = logging.getLogger(__name__)
        
        try:
            slots = handler_input.request_envelope.request.intent.slots
            bucket_name = slots.get("bucketName", {}).value if slots else None
            
            if not bucket_name:
                s3_client = boto3.client('s3')
                buckets = [b['Name'] for b in s3_client.list_buckets()['Buckets']]
                speak_output = (
                    f"You have {len(buckets)} S3 buckets. Please specify which bucket to analyze. "
                    f"For example: 'analyze {buckets[0]} for cost savings'"
                )
                return handler_input.response_builder.speak(speak_output).ask(speak_output).response
            
            s3_client = boto3.client('s3')
            
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                
                paginator = s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=bucket_name, PaginationConfig={'MaxItems': 1000})
                
                total_objects = 0
                total_size = 0
                old_objects = 0
                large_objects = 0
                now = datetime.now(timezone.utc)
                
                for page in pages:
                    for obj in page.get('Contents', []):
                        total_objects += 1
                        size = obj.get('Size', 0)
                        total_size += size
                        
                        last_modified = obj.get('LastModified')
                        if last_modified and (now - last_modified) > timedelta(days=30):
                            old_objects += 1
                        
                        if size > 100 * 1024 * 1024:
                            large_objects += 1
                
                suggestions = []
                if old_objects > 0:
                    suggestions.append(f"Move {old_objects} old files to S3 Infrequent Access")
                if large_objects > 0:
                    suggestions.append(f"Archive {large_objects} large files to Glacier")
                if total_size > 500 * 1024 * 1024:
                    suggestions.append("Set up lifecycle policies")
                
                size_mb = total_size / (1024 * 1024)
                if suggestions:
                    speak_output = (
                        f"Cost analysis for {bucket_name}: {total_objects} objects ({size_mb:.1f} MB). "
                        f"Suggestions: {'; '.join(suggestions)}"
                    )
                else:
                    speak_output = (
                        f"{bucket_name} is well optimized with {total_objects} objects "
                        f"({size_mb:.1f} MB). No recommendations needed."
                    )
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchBucket':
                    speak_output = f"Bucket {bucket_name} doesn't exist. Please check the name and try again."
                elif error_code == 'AccessDenied':
                    speak_output = f"I don't have permission to access {bucket_name}. Please check IAM permissions."
                else:
                    speak_output = f"Couldn't analyze {bucket_name} due to AWS error: {error_code}"
                
            return handler_input.response_builder.speak(speak_output).ask("What would you like to do next?").response
            
        except Exception as e:
            logger.error(f"Error in cost optimization: {str(e)}")
            speak_output = "Sorry, I encountered an error processing your request. Please try again."
            return handler_input.response_builder.speak(speak_output).ask(speak_output).response

class DownloadFileFromS3IntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DownloadFileFromSIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        slots = handler_input.request_envelope.request.intent.slots

        file_name = slots.get("fileName", {}).value
        bucket_name = slots.get("bucketName", {}).value

        if file_name:
            file_name = file_name.replace(" dot ", ".")
            parts = file_name.split()
            common_extensions = ['jpeg', 'jpg', 'png', 'txt', 'pdf', 'doc', 'docx', 'mp3', 'mp4', 'wav']
            
            if len(parts) >= 2:
                last_part = parts[-1].lower()
                if last_part in common_extensions:
                    base_name = " ".join(parts[:-1])
                    file_name = f"{base_name}.{last_part}"
            
            file_name = file_name.replace(".text", ".txt")
            file_name = file_name.replace(" dot text", ".txt")
            file_name = file_name.replace(" text", ".txt")
            file_name = file_name.replace(" ", "_")

        if not file_name or not bucket_name:
            speak_output = "Please specify both a file name and a bucket name. For example, 'Download hello txt from angadangad'."
            reprompt_text = "What file would you like to download and from which bucket?"
            return (
                handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
            )

        request_id = f"{user_id}-download-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            download_table = dynamodb.Table('VirtualAssistant-FileDownloadRequest')
            download_table.put_item(
                Item={
                    'request_id': request_id,
                    'user_id': user_id,
                    'file_name': file_name,
                    'bucket_name': bucket_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': 'pending',
                    'expiration_time': int(time.time()) + 3600
                }
            )

            speak_output = f"I've queued your request to download {file_name} from {bucket_name} to your local folder. Your local agent will process this shortly."
            reprompt_text = "What else can I help you with?"

        except Exception as e:
            logger.error(f"Exception in DownloadFileFromS3IntentHandler: {e}")
            speak_output = "Sorry, I couldn't process your download request. Please try again later."
            reprompt_text = "What else can I help you with?"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(reprompt_text)
            .response
        )

class SetupLifecyclePolicyIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SetupLifecyclePolicyIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        slots = handler_input.request_envelope.request.intent.slots
        
        bucket_name = slots.get("bucketName", {}).value
        
        if not bucket_name:
            speak_output = "Please specify which bucket you'd like to set up lifecycle policies for."
            reprompt_text = "Which bucket should I optimize?"
            return (
                handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
            )
        
        try:
            s3 = boto3.client('s3')
            
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'CostOptimizationRule',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            },
                            {
                                'Days': 365,
                                'StorageClass': 'DEEP_ARCHIVE'
                            }
                        ]
                    }
                ]
            }
            
            s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            
            speak_output = f"Great! I've set up a lifecycle policy for {bucket_name}. Files will automatically move to cheaper storage: Standard IA after 30 days, Glacier after 90 days, and Deep Archive after 365 days. This will save you money!"
            reprompt_text = "Would you like to set up policies for other buckets?"
            
        except Exception as e:
            logger.error(f"Error setting up lifecycle policy: {e}")
            speak_output = f"Sorry, I couldn't set up the lifecycle policy for {bucket_name}. Please make sure the bucket exists and try again."
            reprompt_text = "What else can I help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = """I can help you with several things:
        - Say hello to get a personalized greeting
        - Ask about your friends or add new friends
        - Get weather information
        - Ask for your usage statistics
        - And much more! What would you like to try?"""
        
        reprompt_text = "What can I help you with? You can ask about friends, weather, or say hello."
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        user_profile = DynamoDBHelper.get_user_profile(user_id)
        name = user_profile.get('name', '') if user_profile else ''
        
        speak_output = f"Goodbye{' ' + name if name else ''}! Have a great day!"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .with_should_end_session(True)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = f"You just triggered {intent_name}. What would you like to do next?"
        reprompt_text = "What can I help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."
        reprompt_text = "What can I help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )



sb = SkillBuilder()

sb.add_global_request_interceptor(RequestLoggerInterceptor())
sb.add_global_response_interceptor(ResponseLoggerInterceptor())

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(FriendsNameIntentHandler())
sb.add_request_handler(AddFriendIntentHandler())
sb.add_request_handler(GetStatsIntentHandler())
sb.add_request_handler(WeatherIntentHandler())
sb.add_request_handler(CreateS3BucketIntentHandler())
sb.add_request_handler(ListS3BucketsIntentHandler())
sb.add_request_handler(UploadFileToS3IntentHandler())
sb.add_request_handler(GetCostOptimizationSuggestionsIntentHandler())
sb.add_request_handler(DownloadFileFromS3IntentHandler())
sb.add_request_handler(SetupLifecyclePolicyIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
