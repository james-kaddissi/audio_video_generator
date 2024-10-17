FROM python:3.12.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    libcairo2-dev \
    imagemagick \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Command to run your application
CMD ["python", "src/main.py"]