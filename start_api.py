#!/usr/bin/env python3
"""
Startup script for the alligator.ai API server.
"""

import uvicorn
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.main import app

if __name__ == "__main__":
    # Configuration from environment variables or defaults
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8001))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f"🚀 Starting alligator.ai API server...")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔄 Reload: {reload}")
    print("=" * 50)
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )