#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Formatting colors for clean console output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   Chicago Building Violations API - Setup     ${NC}"
echo -e "${GREEN}===============================================${NC}"

# 1. Ensure the script is being executed from the project root
if [ ! -f "run.py" ]; then
    echo -e "${RED}[ERROR] Please run this script from the project root directory.${NC}"
    echo -e "${RED}        Expected to find run.py in the current directory.${NC}"
    exit 1
fi

# 2. Verify Python 3 Installation
echo -e "${YELLOW}[*] Verifying Python 3 installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed or not added to your PATH.${NC}"
    echo -e "${RED}Please install Python 3 from https://python.org or via your package manager.${NC}"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}[✓] Found $PYTHON_VERSION${NC}"
fi

# 3. Create Python Virtual Environment
echo -e "${YELLOW}[*] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}[✓] Virtual environment created (venv/).${NC}"
else
    echo -e "${GREEN}[✓] Virtual environment already exists. Skipping.${NC}"
fi

# 4. Activate Virtual Environment
echo -e "${YELLOW}[*] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}[✓] Environment active: $(which python)${NC}"

# 5. Upgrade pip
echo -e "${YELLOW}[*] Upgrading pip...${NC}"
python3 -m pip install --upgrade pip --quiet

# 6. Install Dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}[*] Installing project dependencies...${NC}"
    python3 -m pip install -r requirements.txt --quiet
    echo -e "${GREEN}[✓] Dependencies installed successfully.${NC}"
else
    echo -e "${RED}[ERROR] requirements.txt not found!${NC}"
    exit 1
fi

# 7. Check for .env Configuration
echo -e "${YELLOW}[*] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}[!] .env file not found.${NC}"
    echo -e "${YELLOW}[*] Creating template .env file. Please update it with your database credentials.${NC}"
    cp .env.example .env
    echo -e "${GREEN}[✓] Created .env from template. Edit it with your DATABASE_URL before proceeding.${NC}"
    echo -e "${YELLOW}    Open .env and set: DATABASE_URL=postgresql://...${NC}"
    echo ""
    echo -e "${YELLOW}After updating .env, re-run this script or manually run:${NC}"
    echo -e "${GREEN}    source venv/bin/activate${NC}"
    echo -e "${GREEN}    python scripts/ingest.py${NC}"
    echo -e "${GREEN}    python run.py${NC}"
    exit 0
else
    echo -e "${GREEN}[✓] .env file found.${NC}"
fi

# 8. Verify DATABASE_URL is set
if ! grep -q "DATABASE_URL=postgresql" .env 2>/dev/null; then
    echo -e "${RED}[!] DATABASE_URL does not appear to be configured in .env${NC}"
    echo -e "${YELLOW}    Please edit .env with your Supabase connection string.${NC}"
    exit 1
fi

# 9. Run Data Ingestion
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   Running Data Ingestion Pipeline...          ${NC}"
echo -e "${GREEN}===============================================${NC}"

if [ -f "scripts/ingest.py" ]; then
    python3 scripts/ingest.py
else
    echo -e "${RED}[ERROR] scripts/ingest.py not found!${NC}"
    exit 1
fi

# 10. Done
echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   ✓ Setup Complete! Ready to run.             ${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "${YELLOW}To start the server:${NC}"
echo -e "${GREEN}    source venv/bin/activate${NC}"
echo -e "${GREEN}    python run.py${NC}"
echo ""
echo -e "${YELLOW}Then open in your browser:${NC}"
echo -e "${GREEN}    http://localhost:5000        (UI)${NC}"
echo -e "${GREEN}    http://localhost:5000/docs   (Swagger API Docs)${NC}"
echo ""
echo -e "${YELLOW}To run tests:${NC}"
echo -e "${GREEN}    pytest tests/ -v${NC}"
