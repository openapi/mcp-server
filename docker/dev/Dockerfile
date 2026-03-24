FROM python:3.13-slim

# Working directory
WORKDIR /app

# Install dependencies + debugpy
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir debugpy

# Copy application source
COPY . .

# App port (8080) + debugpy port (5678)
EXPOSE 8080 5678

# Required so `import openapi_mcp_sdk` resolves from /app/src
ENV PYTHONPATH=/app/src

# Disable debugpy source-file validation (avoids false "file not found" warnings
# when the container filesystem doesn't match the host path exactly).
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

# Start the server wrapped by debugpy.
# debugpy listens on 0.0.0.0:5678 and the server starts immediately
# (without --wait-for-client) so the MCP endpoint is reachable even when
# no debugger is attached.  Attach from VS Code at any time using the
# "Docker: Attach to MCP (debugpy)" launch configuration.
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", \
     "-m", "openapi_mcp_sdk.main"]
