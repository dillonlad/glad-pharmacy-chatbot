FROM public.ecr.aws/lambda/python:3.12

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application
COPY . /var/task

# Set the Lambda handler
CMD ["main.lambda_handler"]
