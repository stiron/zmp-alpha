# Use the specified Python image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \    
    && rm -rf /var/lib/apt/lists/*

# Clone the specific application from your repository
RUN git clone --depth 1 --branch main --single-branch https://github.com/stiron/zmp-alpha.git . && \
    mv src/alpha_chatbot/* . && \
    rm -rf src

# Install Python dependencies
RUN pip3 install -r ./requirements.txt

# Expose the port the app runs on
EXPOSE 8502

# Define health check for the container
HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health || exit 1

# Command to run the application
ENTRYPOINT ["streamlit", "run", "alpha_chatbot.py", "--server.port=8502", "--server.address=localhost"]

