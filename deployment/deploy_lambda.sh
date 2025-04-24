#!/bin/bash

# Create a deployment package for AWS Lambda
# This script creates a ZIP file with your code and dependencies

echo "Creating Lambda deployment package..."

# Create a temporary directory for the package
PACKAGE_DIR="lambda_package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy the Lambda function code
cp ../Backend/agent_lambda.py $PACKAGE_DIR/
cp ../Backend/.env $PACKAGE_DIR/ 2>/dev/null || echo "No .env file found, make sure to set environment variables in Lambda console"

# Install dependencies into the package directory
echo "Installing dependencies..."
pip install -r ../Backend/requirements.txt -t $PACKAGE_DIR/ --upgrade

# Create the ZIP file
echo "Creating ZIP archive..."
cd $PACKAGE_DIR
zip -r ../lambda_deployment.zip .
cd ..

echo "Deployment package created: lambda_deployment.zip"
echo "You can now upload this package to AWS Lambda."
echo ""
echo "Don't forget to configure these environment variables in your Lambda function:"
echo "- API_KEY: Your API key for the model"
echo "- OPENAI_API_KEY: Your OpenAI API key"
echo "- NEON_API_KEY: Your Neon API key"
echo "- MCP_SERVER_URL: Your MCP server URL"

# Optional: Upload to AWS Lambda if AWS CLI is configured
if command -v aws &> /dev/null; then
    echo ""
    echo "AWS CLI detected. Do you want to upload the package to AWS Lambda? (y/n)"
    read upload_choice
    
    if [ "$upload_choice" = "y" ] || [ "$upload_choice" = "Y" ]; then
        echo "Enter the name of your Lambda function:"
        read lambda_name
        
        echo "Uploading to Lambda function: $lambda_name"
        aws lambda update-function-code --function-name $lambda_name --zip-file fileb://lambda_deployment.zip
        
        echo "Upload complete. Check the AWS Lambda console for more details."
    else
        echo "Skipping AWS upload. You can manually upload the ZIP file from the AWS Lambda console."
    fi
else
    echo ""
    echo "AWS CLI not detected. Please upload the ZIP file manually from the AWS Lambda console."
fi 