FROM public.ecr.aws/lambda/python:3.9

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY agent_lambda.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "agent_lambda.lambda_handler" ]


