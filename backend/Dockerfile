# -------------------------------------------------------------
#  Vault Backend – FastAPI + SQLite + AES‑GCM encryption
# -------------------------------------------------------------
# Use the official slim Python image (small footprint)
FROM python:3.12-slim AS base

# 1️⃣ OS‑level dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2️⃣ Create a non‑root user for safety
ARG USER=appuser
ARG UID=1000
ARG GID=1000
RUN addgroup --gid $GID $USER && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" $USER

# 3️⃣ Set working directory
WORKDIR /app

# 4️⃣ Install Python dependencies
#    (copy only the files needed for installing)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy the source code (including the SQLite DB files)
COPY . .

# 6️⃣ Expose the FastAPI port
EXPOSE 8000

# 7️⃣ Switch to the non‑root user
USER $USER

# 8️⃣ Run the API with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
