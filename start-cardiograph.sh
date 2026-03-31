#!/bin/bash

# CardioGraph Startup Script
# This script starts both the backend and frontend servers

echo "🫀 Starting CardioGraph Medical Knowledge Graph System..."
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Neo4j is running
echo -e "${YELLOW}Checking Neo4j...${NC}"
if docker ps | grep -q graph-rag-neo4j; then
    echo -e "${GREEN}✓ Neo4j is running${NC}"
else
    echo -e "${RED}✗ Neo4j is not running${NC}"
    echo -e "${YELLOW}Starting Neo4j container...${NC}"
    docker start graph-rag-neo4j
    sleep 5
    echo -e "${GREEN}✓ Neo4j started${NC}"
fi

# Check if Ollama is accessible
echo -e "${YELLOW}Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is accessible${NC}"
else
    echo -e "${RED}✗ Ollama is not accessible${NC}"
    echo -e "${YELLOW}Please start Ollama service${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}Starting services...${NC}"
echo "=================================================="
echo ""

# Start backend in background
echo -e "${YELLOW}Starting FastAPI Backend on port 8000...${NC}"
cd "$(dirname "$0")"
python -m uvicorn graph_rag.api:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Start frontend in background
echo -e "${YELLOW}Starting React Frontend on port 3000...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo "=================================================="
echo -e "${GREEN}🫀 CardioGraph is ready!${NC}"
echo "=================================================="
echo ""
echo -e "${GREEN}Access Points:${NC}"
echo -e "  Frontend:  ${YELLOW}http://localhost:3000${NC}"
echo -e "  Backend:   ${YELLOW}http://localhost:8000${NC}"
echo -e "  API Docs:  ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Neo4j:     ${YELLOW}http://localhost:7474${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:   tail -f backend.log"
echo -e "  Frontend:  tail -f frontend.log"
echo ""
echo -e "${RED}To stop:${NC} Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Save PIDs to file
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user interrupt
trap "echo -e '\n${YELLOW}Shutting down...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; echo -e '${GREEN}✓ Stopped${NC}'; exit" INT TERM

# Keep script running
wait
