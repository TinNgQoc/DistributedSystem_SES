#!/bin/bash
# SES Distributed System Demo Runner (Bash)
# Launches multiple process instances for testing SES implementation

set -e

# Default configuration
PROCESS_COUNT=15
SCENARIO="normal"
DURATION=300
INTERACTIVE=false
CLEAN_LOGS=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to show usage
show_help() {
    echo "SES Demo Runner - Bash Script"
    echo "Usage: ./run_demo.sh [options]"
    echo "Options:"
    echo "  -c <num>     Process count (default: 15)"
    echo "  -s <name>    Scenario: normal/small/stress"
    echo "  -d <sec>     Duration in seconds (default: 300)"
    echo "  -i           Interactive mode"
    echo "  -l           Clean logs before starting"
    echo "  -h           Show help"
}

# Parse arguments
while getopts "c:s:d:ilh" opt; do
    case $opt in
        c) PROCESS_COUNT=$OPTARG ;;
        s) SCENARIO=$OPTARG ;;
        d) DURATION=$OPTARG ;;
        i) INTERACTIVE=true ;;
        l) CLEAN_LOGS=true ;;
        h) show_help; exit 0 ;;
        *) show_help; exit 1 ;;
    esac
done

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON_SCRIPT="$SCRIPT_DIR/run_node.py"

# Process tracking
declare -a PROCESS_PIDS=()
START_TIME=$(date +%s)

echo -e "${GREEN}🚀 SES Distributed System Demo Runner${NC}"
echo -e "${GREEN}====================================${NC}"

# Clean logs if requested
if [[ "$CLEAN_LOGS" == true ]]; then
    echo "🧹 Cleaning log directory..."
    rm -rf "$LOG_DIR"
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Configure scenario
case "$SCENARIO" in
    "small") PROCESS_COUNT=5 ;;
    "stress") PROCESS_COUNT=15 ;;
esac

echo "📊 Configuration:"
echo "  Processes: $PROCESS_COUNT"
echo "  Duration: $DURATION seconds"
echo "  Log Directory: $LOG_DIR"
echo ""

# Function to start a process
start_ses_process() {
    local process_id=$1
    local log_file="$LOG_DIR/pid_${process_id}.txt"
    
    cd "$SCRIPT_DIR"
    python3 run_node.py $process_id > "$log_file" 2>&1 &
    local pid=$!
    PROCESS_PIDS+=($pid)
    echo -e "${GREEN}🟢 Started Process $process_id (PID: $pid)${NC}"
}

# Function to cleanup processes
cleanup_processes() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping all processes...${NC}"
    
    for pid in "${PROCESS_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    sleep 2
    
    for pid in "${PROCESS_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Setup signal handlers
trap cleanup_processes EXIT INT TERM

# Main execution
echo ""
echo -e "${GREEN}🚀 Starting $PROCESS_COUNT processes...${NC}"

for ((i=0; i<PROCESS_COUNT; i++)); do
    start_ses_process $i
    sleep 0.5
done

echo ""
echo -e "${GREEN}✅ All processes started!${NC}"
echo -e "${CYAN}📁 Log files available in: $LOG_DIR${NC}"
echo -e "${YELLOW}⏱️  Running for $DURATION seconds...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop early${NC}"

# Wait for duration
sleep $DURATION

echo ""
echo -e "${GREEN}🏁 Demo completed!${NC}"
