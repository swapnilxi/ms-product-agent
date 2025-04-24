# AWS Lambda Deployment Guide for MCPAgent

This guide explains how to deploy your MCPAgent to AWS Lambda with API Gateway.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- AWS SAM CLI installed (for CloudFormation deployment)
- Python 3.9
- Necessary API keys (OpenAI, Neon)

## Option 1: Manual Deployment

### Step 1: Create the Deployment Package

Run the provided script to create your deployment package:

```bash
cd deployment
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

This script will:
1. Create a temporary directory
2. Copy your Lambda code
3. Install dependencies
4. Create a ZIP file (`lambda_deployment.zip`)

### Step 2: Create Lambda Function in AWS Console

1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Enter function name (e.g., "MCPAgent")
5. Choose Runtime: Python 3.9
6. Create the function

### Step 3: Upload Deployment Package

1. In the Lambda function page, click "Upload from" and select "ZIP file"
2. Upload the `lambda_deployment.zip` file

### Step 4: Configure Environment Variables

In the Lambda function configuration, add these environment variables:

- `API_KEY`: Your API key for the model
- `OPENAI_API_KEY`: Your OpenAI API key
- `NEON_API_KEY`: Your Neon API key
- `MCP_SERVER_URL`: Your MCP server URL (e.g., https://mcp.neon.tech/sse)

### Step 5: Configure Lambda Settings

1. Increase timeout to 5 minutes (300 seconds)
2. Increase memory to at least 1024 MB
3. Configure IAM role with basic Lambda execution permissions

### Step 6: Set Up API Gateway

1. Add an API Gateway trigger
2. Create a new REST API
3. Configure with open security (for testing) or API key (for production)
4. Deploy the API

## Option 2: CloudFormation Deployment

### Step 1: Create the Deployment Package

Run the deployment script as in Option 1.

### Step 2: Deploy with AWS SAM

```bash
# Install AWS SAM CLI if you haven't already
pip install aws-sam-cli

# Deploy using SAM
cd deployment
sam deploy --guided --template-file template.yaml
```

Follow the prompts to:
1. Enter a stack name
2. Choose AWS region
3. Enter your API keys
4. Confirm deployment

### Step 3: Test Your Deployment

```bash
# The SAM deployment will output your API Gateway URL
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/agent \
  -H "Content-Type: application/json" \
  -d '{"task": "What are products available at microsoft?", "message_type": "text"}'
```

## Troubleshooting

### Common Issues:

1. **Deployment Package Too Large**: 
   - Use Lambda Layers for dependencies
   - Remove unnecessary libraries

2. **Timeout Errors**:
   - Increase Lambda timeout (up to 15 minutes)
   - Optimize code for faster execution

3. **Memory Errors**:
   - Increase Lambda memory allocation
   - Consider optimizing image processing if using it

4. **Permissions Issues**:
   - Check CloudWatch logs for specific permission errors
   - Ensure Lambda execution role has necessary permissions

5. **API Gateway Errors**:
   - Verify API Gateway configuration
   - Check CORS settings if calling from browser

### Viewing Logs:

Check CloudWatch Logs to troubleshoot issues:
1. Go to AWS CloudWatch console
2. Navigate to Log groups
3. Find `/aws/lambda/MCPAgent` (or your function name)
4. View log streams for detailed error messages 