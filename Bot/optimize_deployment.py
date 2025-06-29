#!/usr/bin/env python3
"""
Deployment optimization script for different hosting platforms.
Run this script before deploying to apply platform-specific optimizations.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import DeploymentProfiles, OptimizationConfig


def setup_deployment(platform: str):
    """Setup deployment configuration for a specific platform."""

    print(f"🚀 Setting up deployment for {platform.upper()}")

    # Apply the platform-specific profile
    try:
        DeploymentProfiles.apply_profile(platform)
        print(f"✅ Applied {platform} optimization profile")
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False

    # Create .env file with optimized settings
    env_content = f"""# Optimized settings for {platform.upper()} deployment
# Generated automatically - do not edit manually

# Model settings
EMBEDDING_MODEL={OptimizationConfig.EMBEDDING_MODEL}
LLM_MODEL={OptimizationConfig.LLM_MODEL}

# Memory optimization
MAX_CHUNKS={OptimizationConfig.MAX_CHUNKS}
BATCH_SIZE={OptimizationConfig.BATCH_SIZE}
TOP_K_RESULTS={OptimizationConfig.TOP_K_RESULTS}

# Chunking settings
MAX_TOKENS_PER_CHUNK={OptimizationConfig.MAX_TOKENS_PER_CHUNK}
CHUNK_OVERLAP={OptimizationConfig.CHUNK_OVERLAP}

# Storage settings
ENABLE_COMPRESSION={str(OptimizationConfig.ENABLE_COMPRESSION).lower()}

# Memory management
UNLOAD_MODEL_AFTER_USE={str(OptimizationConfig.UNLOAD_MODEL_AFTER_USE).lower()}

# Add your API keys here:
# GROQ_API_KEY=your_groq_api_key_here
"""

    env_file = current_dir / ".env"
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"📝 Created optimized .env file: {env_file}")

    # Create deployment-specific docker settings if needed
    if platform == "render":
        create_render_dockerfile()
    elif platform == "railway":
        create_railway_config()

    print("\n📋 Deployment Summary:")
    print(f"   Platform: {platform.upper()}")
    print(f"   Max Chunks: {OptimizationConfig.MAX_CHUNKS}")
    print(f"   Chunk Size: {OptimizationConfig.MAX_TOKENS_PER_CHUNK} tokens")
    print(f"   Model: {OptimizationConfig.EMBEDDING_MODEL}")
    print(f"   LLM: {OptimizationConfig.LLM_MODEL}")
    print(
        f"   Compression: {'Enabled' if OptimizationConfig.ENABLE_COMPRESSION else 'Disabled'}"
    )

    print("\n🔑 Next Steps:")
    print("1. Add your GROQ_API_KEY to the .env file")
    print("2. Test locally with: python -m uvicorn app.main:app --reload")
    print("3. Deploy to your platform")

    return True


def create_render_dockerfile():
    """Create optimized Dockerfile for Render."""
    dockerfile_content = """# Optimized Dockerfile for Render deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
"""

    dockerfile_path = current_dir / "Dockerfile.render"
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    print(f"🐳 Created Render-optimized Dockerfile: {dockerfile_path}")


def create_railway_config():
    """Create Railway-specific configuration."""
    railway_toml = """[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[environments.production.variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
"""

    railway_path = current_dir / "railway.toml"
    with open(railway_path, "w") as f:
        f.write(railway_toml)

    print(f"🚂 Created Railway configuration: {railway_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Optimize RAG bot deployment for different platforms"
    )
    parser.add_argument(
        "platform",
        choices=["render", "vercel", "railway"],
        help="Target deployment platform",
    )

    args = parser.parse_args()

    success = setup_deployment(args.platform)

    if success:
        print(
            f"\n🎉 Deployment optimization for {args.platform.upper()} completed successfully!"
        )
        sys.exit(0)
    else:
        print(f"\n💥 Deployment optimization for {args.platform.upper()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
