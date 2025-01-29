# Base image with Python and CUDA for GPU support (if needed)
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# Set environment variables to prevent Python from buffering outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install necessary tools and Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as the default
RUN ln -s /usr/bin/python3 /usr/bin/python

# Copy the requirements file
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy the fine-tuning script and other necessary files
COPY gemini_fine_tuning.py /app/gemini_fine_tuning.py

# Set the working directory
WORKDIR /app

# Command to run your fine-tuning script
CMD ["python", "gemini_fine_tuning.py"]
