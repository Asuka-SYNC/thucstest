# Stage 1: Build frontend
FROM node:20 AS frontend-build
WORKDIR /app
# Set npm registry to PKU mirror
RUN npm config set registry https://mirrors.pku.edu.cn/npm/
COPY package.json vite.config.js index.html ./
COPY src/ ./src
COPY public/ ./public
RUN npm install
RUN npm run build

# Stage 2: Setup backend
FROM python:3.12-slim AS backend
WORKDIR /app
# Install system dependencies (mariadb client, build tools)
RUN apt-get update && apt-get install -y build-essential libmariadb-dev mariadb-client && rm -rf /var/lib/apt/lists/*
# Set pip to use PKU mirror
RUN pip config set global.index-url https://mirrors.pku.edu.cn/pypi/web/simple
# Install uv for fast dependency management
RUN pip install uv
# Copy only dependency files first for build cache
COPY pyproject.toml ./
RUN uv pip install -r pyproject.toml --system
# Copy backend code after dependencies are installed
COPY backend/ ./backend
# Copy built frontend
COPY --from=frontend-build /app/dist ./frontend_dist
# Expose port
EXPOSE 8000
# Set environment variables for MariaDB connection
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USER=thucs2pl
ENV DB_PASSWORD=thucs2plpass
ENV DB_NAME=thucs2pl_db
ENV PYTHONUNBUFFERED=1
# Start backend server
CMD ["python", "backend/main.py"]
