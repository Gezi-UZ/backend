FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv with lockfile
RUN uv pip install -r pyproject.toml

# Copy the rest of the application
COPY . .

# Copy and make the start script executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port (documentational, Railway uses $PORT)
EXPOSE 8000

# Command to run the application
CMD ["/start.sh"]
