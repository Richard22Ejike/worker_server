FROM runpod/base:0.4.0-cuda11.8.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /worker

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your application code
COPY . .

# Command to run your application
CMD ["python", "-u", "/worker/main.py"]