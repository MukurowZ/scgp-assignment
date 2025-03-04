# Use a Bun base image
ARG BUN_VERSION=1.1.34
FROM oven/bun:${BUN_VERSION}-slim as base

# Set the working directory in the container
WORKDIR /app

# Install necessary global dependencies (like http-server and Vite, if needed)
RUN bun add vite --global

# Copy package.json and bun.lockb to install dependencies before copying the entire codebase
COPY package.json ./

# Install dependencies
RUN bun install

EXPOSE 5173

# Mount the local frontend code into the container (development purpose)
# Use volumes in Docker Compose to ensure changes reflect without rebuilding
CMD ["bun", "run", "dev"]
