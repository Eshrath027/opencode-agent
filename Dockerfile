FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user FIRST
RUN useradd -m -u 1000 opencodeuser

# Switch to non-root user for installation
USER opencodeuser

# Install OpenCode CLI as non-root user
RUN curl -fsSL https://opencode.ai/install | bash

# Add user's local bin to PATH
ENV PATH="/home/opencodeuser/.local/bin:${PATH}"

# Set working directory
WORKDIR /workspace

# COPY opencode.json /workspace/opencode.json

RUN mkdir -p /home/opencodeuser/.config/opencode
COPY opencode.json /home/opencodeuser/.config/opencode/config.json
COPY AGENTS.md /home/opencodeuser/.config/opencode/AGENTS.md

# Switch back to root briefly to set permissions
USER root
RUN chown -R opencodeuser:opencodeuser /workspace
# Switch back to non-root user
USER opencodeuser

ENV PATH="/home/opencodeuser/.opencode/bin:${PATH}"
CMD ["bash"]