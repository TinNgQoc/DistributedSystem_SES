#!/usr/bin/env python3
"""
Simple Test CLI for SES Distributed System
Quick testing and validation tool before running full demo
"""

import sys
import os
import json
import time
import threading
from typing import Dict, List, Any
import argparse
import logging

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ses_clock import SESClock
from buffer_manager import BufferManager
from deliver_engine import DeliverEngine
from network_manager import NetworkManager, NetworkMessage
from config_loader import ConfigManager

class SESTestCLI:
    """Simple test CLI for validating SES components"""
    
    def __init__(self):
        self.setup_logging()
        self.config = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def setup_logging(self):
        """Setup logging for tests"""
        logging.basicConfig(
            level=logging.WARNING,  # Reduce noise during tests
            format='%(levelname)s: %(message)s'
        )
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.tests_failed += 1
            print(f"❌ {test_name}: FAILED {message}")
    
    def test_config_loading(self):
        """Test configuration loading"""
        print("\n🧪 Testing Configuration Loading...")
        
        try:
            config_manager = ConfigManager("config.json")
            if config_manager.validate():
                self.config = config_manager.get_config()
                self.log_test("Config Loading", True, f"- {len(self.config['processes'])} processes configured")
                
                # Test config content
                if len(self.config['processes']) == 15:
                    self.log_test("Process Count", True, "- Exactly 15 processes")
                else:
                    self.log_test("Process Count", False, f"- Expected 15, got {len(self.config['processes'])}")
                
                # Test port uniqueness
                ports = [p['port'] for p in self.config['processes']]
                if len(ports) == len(set(ports)):
                    self.log_test("Port Uniqueness", True, "- All ports are unique")
                else:
                    self.log_test("Port Uniqueness", False, "- Duplicate ports found")
                
            else:
                self.log_test("Config Loading", False, f"- {config_manager.get_error()}")
                
        except Exception as e:
            self.log_test("Config Loading", False, f"- Exception: {e}")
    
    def test_ses_clock(self):
        """Test SES vector clock implementation"""
        print("\n🧪 Testing SES Vector Clock...")
        
        try:
            # Create test clocks
            clock0 = SESClock(0, 3)
            clock1 = SESClock(1, 3)
            clock2 = SESClock(2, 3)
            
            # Test initial state
            initial = clock0.get()
            if initial == [0, 0, 0]:
                self.log_test("Clock Initialization", True, "- Initial state [0,0,0]")
            else:
                self.log_test("Clock Initialization", False, f"- Expected [0,0,0], got {initial}")
            
            # Test local tick
            clock0.tick()
            after_tick = clock0.get()
            if after_tick == [1, 0, 0]:
                self.log_test("Local Tick", True, "- P0 tick: [0,0,0] -> [1,0,0]")
            else:
                self.log_test("Local Tick", False, f"- Expected [1,0,0], got {after_tick}")
            
            # Test message receive
            clock1.update_on_receive(0, [1, 0, 0])
            after_receive = clock1.get()
            if after_receive == [1, 1, 0]:
                self.log_test("Message Receive", True, "- P1 receive from P0: [0,0,0] -> [1,1,0]")
            else:
                self.log_test("Message Receive", False, f"- Expected [1,1,0], got {after_receive}")
            
            # Test SES delivery condition
            can_deliver = clock2.can_deliver_ses([1, 1, 0], 1)
            if not can_deliver:  # P2 hasn't seen any events, so should NOT be able to deliver
                self.log_test("SES Condition - Cannot Deliver", True, "- Correctly blocks delivery (P2 behind)")
            else:
                self.log_test("SES Condition - Cannot Deliver", False, "- Should block delivery")
            
            # Test causality gap  
            gap = clock2.get_causality_gap([2, 1, 0], 0)
            if gap == {1: 1}:  # P2 should only be missing events from P1
                self.log_test("Causality Gap", True, f"- Gap calculation: {gap}")
            else:
                self.log_test("Causality Gap", False, f"- Expected {{1: 1}}, got {gap}")
                
        except Exception as e:
            self.log_test("SES Clock", False, f"- Exception: {e}")
    
    def test_buffer_manager(self):
        """Test buffer manager implementation"""
        print("\n🧪 Testing Buffer Manager...")
        
        try:
            delivered_messages = []
            buffered_messages = []
            
            def mock_ses_checker(message):
                # Simple rule: deliver if seq <= 2
                return message['seq'] <= 2
            
            def on_delivered(message):
                delivered_messages.append(message)
            
            def on_buffered(message):
                buffered_messages.append(message)
            
            # Create buffer manager
            buffer_mgr = BufferManager(0, mock_ses_checker)
            buffer_mgr.on_message_delivered = on_delivered
            buffer_mgr.on_message_buffered = on_buffered
            buffer_mgr.start()
            
            # Test messages
            msg1 = {"sender_id": 1, "seq": 1, "vector_clock": [0, 1, 0]}  # Should deliver
            msg2 = {"sender_id": 1, "seq": 3, "vector_clock": [0, 3, 0]}  # Should buffer
            msg3 = {"sender_id": 1, "seq": 2, "vector_clock": [0, 2, 0]}  # Should deliver
            
            # Test immediate delivery
            delivered, cascaded = buffer_mgr.try_deliver_message(msg1)
            if delivered and len(delivered_messages) == 1:
                self.log_test("Immediate Delivery", True, "- Message 1 delivered immediately")
            else:
                self.log_test("Immediate Delivery", False, f"- Expected delivery, got {delivered}")
            
            # Test buffering
            delivered, cascaded = buffer_mgr.try_deliver_message(msg2)
            # Check if message was buffered (buffered_messages callback should be called)
            if len(buffered_messages) == 1 and len(cascaded) == 0:
                self.log_test("Message Buffering", True, "- Message 3 buffered correctly")
            else:
                self.log_test("Message Buffering", False, f"- Expected buffering, buffered_count={len(buffered_messages)}, cascaded_count={len(cascaded)}")
            
            # Test buffer state
            buffer_state = buffer_mgr.get_buffer_state()
            if buffer_state['buffer_size'] == 1:
                self.log_test("Buffer State", True, f"- Buffer size: {buffer_state['buffer_size']}")
            else:
                self.log_test("Buffer State", False, f"- Expected size 1, got {buffer_state['buffer_size']}")
            
            buffer_mgr.stop()
            
        except Exception as e:
            self.log_test("Buffer Manager", False, f"- Exception: {e}")
    
    def test_delivery_engine(self):
        """Test message delivery engine"""
        print("\n🧪 Testing Delivery Engine...")
        
        try:
            processed_messages = []
            
            def process_message(message):
                processed_messages.append(message)
            
            # Create delivery engine
            engine = DeliverEngine(0, process_message)
            engine.start()
            
            # Test message preparation
            outgoing = engine.send_message(1, 1, "Test message")
            expected_keys = {"sender_id", "receiver_id", "seq", "vector_clock", "payload", "timestamp"}
            if all(key in outgoing for key in expected_keys):
                self.log_test("Message Preparation", True, "- All required fields present")
            else:
                self.log_test("Message Preparation", False, "- Missing required fields")
            
            # Test clock update on send
            clock_after_send = engine.get_current_clock()
            if clock_after_send[0] == 1:  # Process 0 should have incremented
                self.log_test("Clock Update on Send", True, f"- Clock: {clock_after_send}")
            else:
                self.log_test("Clock Update on Send", False, f"- Unexpected clock: {clock_after_send}")
            
            # Test message reception
            incoming = {
                "sender_id": 1,
                "receiver_id": 0,
                "seq": 1,
                "vector_clock": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Full 15-element clock
                "payload": "Test response",
                "timestamp": "2025-01-01T12:00:00"
            }
            
            success = engine.receive_message(incoming)
            if success and len(processed_messages) > 0:
                self.log_test("Message Reception", True, "- Message received and processed")
            else:
                self.log_test("Message Reception", False, "- Message not processed")
            
            # Test statistics
            stats = engine.get_delivery_stats()
            if stats['total_delivered'] > 0:
                self.log_test("Delivery Statistics", True, f"- {stats['total_delivered']} messages delivered")
            else:
                self.log_test("Delivery Statistics", False, "- No deliveries recorded")
            
            engine.stop()
            
        except Exception as e:
            self.log_test("Delivery Engine", False, f"- Exception: {e}")
    
    def test_network_basics(self):
        """Test basic network functionality (without actual connections)"""
        print("\n🧪 Testing Network Components...")
        
        if not self.config:
            self.log_test("Network Components", False, "- No config available")
            return
        
        try:
            # Test message creation
            msg = NetworkMessage(0, 1, 1, [1, 0, 0], "Test payload")
            msg_dict = msg.to_dict()
            
            expected_keys = {"sender_id", "receiver_id", "seq", "vector_clock", "payload", "timestamp"}
            if all(key in msg_dict for key in expected_keys):
                self.log_test("Network Message Creation", True, "- All fields present")
            else:
                self.log_test("Network Message Creation", False, "- Missing fields")
            
            # Test message deserialization
            reconstructed = NetworkMessage.from_dict(msg_dict)
            if (reconstructed.sender_id == msg.sender_id and 
                reconstructed.payload == msg.payload):
                self.log_test("Message Serialization", True, "- Round-trip successful")
            else:
                self.log_test("Message Serialization", False, "- Data corruption")
            
            # Test configuration validation
            process_configs = {p['id']: p for p in self.config['processes']}
            if len(process_configs) == 15 and 0 in process_configs:
                self.log_test("Network Configuration", True, "- Process configs valid")
            else:
                self.log_test("Network Configuration", False, "- Invalid process configs")
                
        except Exception as e:
            self.log_test("Network Components", False, f"- Exception: {e}")
    
    def test_integration_basic(self):
        """Test basic integration between components"""
        print("\n🧪 Testing Basic Integration...")
        
        try:
            # Test that components can be created together
            processed_messages = []
            
            def process_message(msg):
                processed_messages.append(msg)
            
            # Create integrated components
            engine = DeliverEngine(0, process_message)
            engine.start()
            
            # Test clock synchronization
            initial_clock = engine.get_current_clock()
            
            # Send a message (updates clock)
            outgoing = engine.send_message(1, 1, "Integration test")
            send_clock = engine.get_current_clock()
            
            if send_clock[0] > initial_clock[0]:
                self.log_test("Clock Integration", True, "- Clock updated on send")
            else:
                self.log_test("Clock Integration", False, "- Clock not updated")
            
            # Receive a message
            incoming = {
                "sender_id": 1, "receiver_id": 0, "seq": 1,
                "vector_clock": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "payload": "Response",
                "timestamp": "2025-01-01T12:00:00"
            }
            
            engine.receive_message(incoming)
            receive_clock = engine.get_current_clock()
            
            # Clock should reflect received message
            if receive_clock[1] > 0:
                self.log_test("Receive Integration", True, f"- Clock after receive: {receive_clock}")
            else:
                self.log_test("Receive Integration", False, "- Clock not updated on receive")
            
            # Check message processing
            if len(processed_messages) > 0:
                self.log_test("Message Processing", True, f"- {len(processed_messages)} messages processed")
            else:
                self.log_test("Message Processing", False, "- No messages processed")
            
            engine.stop()
            
        except Exception as e:
            self.log_test("Integration Basic", False, f"- Exception: {e}")
    
    def run_performance_test(self):
        """Run basic performance test"""
        print("\n🧪 Testing Performance...")
        
        try:
            processed_count = 0
            
            def process_message(msg):
                nonlocal processed_count
                processed_count += 1
            
            # Create engine
            engine = DeliverEngine(0, process_message)
            engine.start()
            
            # Send many messages quickly
            start_time = time.time()
            message_count = 100
            
            for i in range(message_count):
                engine.send_message(1, i+1, f"Perf test {i}")
            
            send_time = time.time() - start_time
            
            # Process received messages
            start_time = time.time()
            
            for i in range(message_count):
                clock_vector = [0] * 15
                clock_vector[1] = i+1  # Update sender's position
                msg = {
                    "sender_id": 1, "receiver_id": 0, "seq": i+1,
                    "vector_clock": clock_vector, "payload": f"Response {i}",
                    "timestamp": "2025-01-01T12:00:00"
                }
                engine.receive_message(msg)
            
            process_time = time.time() - start_time
            
            # Check results
            if send_time < 1.0:  # Should be very fast
                self.log_test("Send Performance", True, f"- {message_count} messages in {send_time:.3f}s")
            else:
                self.log_test("Send Performance", False, f"- Too slow: {send_time:.3f}s")
            
            if process_time < 2.0:  # Processing may be slower due to SES checks
                self.log_test("Process Performance", True, f"- {message_count} messages in {process_time:.3f}s")
            else:
                self.log_test("Process Performance", False, f"- Too slow: {process_time:.3f}s")
            
            if processed_count > 0:
                self.log_test("Message Throughput", True, f"- {processed_count}/{message_count} delivered")
            else:
                self.log_test("Message Throughput", False, "- No messages delivered")
            
            engine.stop()
            
        except Exception as e:
            self.log_test("Performance", False, f"- Exception: {e}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 SES DISTRIBUTED SYSTEM - COMPONENT TESTS")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run test suites
        self.test_config_loading()
        self.test_ses_clock()
        self.test_buffer_manager()
        self.test_delivery_engine()
        self.test_network_basics()
        self.test_integration_basic()
        self.run_performance_test()
        
        # Show results
        elapsed = time.time() - start_time
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 50)
        print("🎯 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Total Time: {elapsed:.2f} seconds")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! System ready for demo.")
            return True
        else:
            print(f"\n⚠️  {self.tests_failed} tests failed. Please fix issues before running demo.")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SES System Test CLI")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--perf", action="store_true", help="Run performance tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    # Create and run tests
    test_cli = SESTestCLI()
    
    if args.quick:
        print("🏃 Running quick tests only...")
        test_cli.test_config_loading()
        test_cli.test_ses_clock()
    elif args.perf:
        print("⚡ Running performance tests only...")
        test_cli.run_performance_test()
    else:
        success = test_cli.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()