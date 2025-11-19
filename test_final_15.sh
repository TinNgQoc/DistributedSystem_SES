#!/bin/bash
# Final test with 15 processes and startup coordination

echo "🎯 FINAL TEST: 15 PROCESSES WITH STARTUP COORDINATION"
echo "=================================================="
echo "Startup delay: 8 seconds"
echo ""

# Clean and start
rm -rf logs
mkdir -p logs

echo "Starting 15 processes..."
for i in {0..14}; do
    echo "  Process $i starting..."
    python3 run_node.py $i > logs/pid_$i.txt 2>&1 &
    sleep 0.3
done

echo "All started. Running for 60 seconds..."
sleep 60

echo ""
echo "Stopping..."
pkill -f "python3 run_node.py"

echo "Results:"
total=0
for i in {0..14}; do
    if [ -f "logs/pid_$i.txt" ]; then
        count=$(grep -c "DELIVERED" logs/pid_$i.txt 2>/dev/null || echo 0)
        total=$((total + count))
        status=""
        if [ $count -ge 150 ]; then
            status="✅"
        elif [ $count -ge 50 ]; then
            status="⚠️"
        else
            status="❌"
        fi
        echo "  P$i: $count messages $status"
    fi
done
echo "Total: $total messages"

# Check for startup coordination
echo ""
echo "Startup coordination verification:"
coordination_count=$(grep -c "Waiting.*seconds for all processes" test_final_150/*.txt 2>/dev/null || echo 0)
echo "Processes that waited for startup: $coordination_count/15"