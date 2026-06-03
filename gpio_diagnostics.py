"""
Vinny Tactical Core - GPIO Diagnostic Tool
Complete hardware testing and validation for all GPIO pins and sensors
"""

import RPi.GPIO as GPIO
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple


class GPIODiagnostics:
    """Comprehensive GPIO diagnostic and testing tool"""
    
    def __init__(self):
        """Initialize diagnostic tool"""
        self.dock_pin = 18
        self.obstacle_pin = 21
        self.test_results = {}
        self.readings_history = []
        
    def setup_gpio(self) -> bool:
        """Initialize GPIO in BCM mode"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            print("✓ GPIO mode set to BCM")
            return True
        except Exception as e:
            print(f"✗ GPIO setup error: {e}")
            return False
    
    def test_dock_pin(self) -> bool:
        """Test dock sensor on GPIO pin 18"""
        print("\n" + "="*60)
        print("DOCK SENSOR TEST (GPIO 18)")
        print("="*60)
        
        try:
            GPIO.setup(self.dock_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            print(f"✓ Pin 18 configured as INPUT with PULL-DOWN")
            print(f"  Expected: LOW (0) when not docked\n")
            
            # Take multiple readings
            readings = []
            for i in range(10):
                state = GPIO.input(self.dock_pin)
                readings.append(state)
                status = "🟢 HIGH (DOCKED)" if state == GPIO.HIGH else "🔴 LOW (NOT DOCKED)"
                print(f"  Reading {i+1:2d}/10: {status}")
                time.sleep(0.1)
            
            # Analyze readings
            high_count = sum(readings)
            low_count = len(readings) - high_count
            stability = (high_count == 10 or low_count == 10)
            
            print(f"\n📊 ANALYSIS:")
            print(f"  HIGH readings: {high_count}/10")
            print(f"  LOW readings:  {low_count}/10")
            print(f"  Stability: {'✓ Stable' if stability else '✗ Unstable (fluctuating)'}")
            
            if high_count >= 8:
                result = 'ACTIVE (DOCKED)'
                print(f"  Status: ✓ Dock sensor ACTIVE")
                self.test_results['dock_pin'] = 'ACTIVE'
            elif low_count >= 8:
                result = 'INACTIVE (NOT DOCKED)'
                print(f"  Status: ✓ Dock sensor INACTIVE")
                self.test_results['dock_pin'] = 'INACTIVE'
            else:
                result = 'UNSTABLE'
                print(f"  Status: ⚠ Dock sensor UNSTABLE (needs debouncing)")
                self.test_results['dock_pin'] = 'UNSTABLE'
            
            return True
            
        except Exception as e:
            print(f"✗ Dock pin test failed: {e}")
            self.test_results['dock_pin'] = 'ERROR'
            return False
    
    def test_obstacle_pin(self) -> bool:
        """Test obstacle sensor on GPIO pin 21"""
        print("\n" + "="*60)
        print("OBSTACLE SENSOR TEST (GPIO 21)")
        print("="*60)
        
        try:
            GPIO.setup(self.obstacle_pin, GPIO.IN)
            print(f"✓ Pin 21 configured as INPUT (no pull-up/pull-down)")
            print(f"  Expected: LOW (0) when path is clear\n")
            
            # Take multiple readings
            readings = []
            for i in range(10):
                state = GPIO.input(self.obstacle_pin)
                readings.append(state)
                status = "🟢 HIGH (OBSTACLE)" if state == GPIO.HIGH else "🔴 LOW (CLEAR)"
                print(f"  Reading {i+1:2d}/10: {status}")
                time.sleep(0.1)
            
            # Analyze readings
            high_count = sum(readings)
            low_count = len(readings) - high_count
            stability = (high_count == 10 or low_count == 10)
            
            print(f"\n📊 ANALYSIS:")
            print(f"  HIGH readings: {high_count}/10")
            print(f"  LOW readings:  {low_count}/10")
            print(f"  Stability: {'✓ Stable' if stability else '✗ Unstable (fluctuating)'}")
            
            if high_count >= 8:
                result = 'OBSTACLE_DETECTED'
                print(f"  Status: ✓ Obstacle DETECTED")
                self.test_results['obstacle_pin'] = 'OBSTACLE_DETECTED'
            elif low_count >= 8:
                result = 'CLEAR'
                print(f"  Status: ✓ Path CLEAR")
                self.test_results['obstacle_pin'] = 'CLEAR'
            else:
                result = 'UNSTABLE'
                print(f"  Status: ⚠ Obstacle sensor UNSTABLE (needs filtering)")
                self.test_results['obstacle_pin'] = 'UNSTABLE'
            
            return True
            
        except Exception as e:
            print(f"✗ Obstacle pin test failed: {e}")
            self.test_results['obstacle_pin'] = 'ERROR'
            return False
    
    def test_pull_configurations(self) -> bool:
        """Test different pull-up and pull-down configurations"""
        print("\n" + "="*60)
        print("PULL-UP/PULL-DOWN CONFIGURATION TEST")
        print("="*60)
        
        try:
            # Test pull-down on dock pin
            GPIO.setup(self.dock_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            dock_with_pull_down = GPIO.input(self.dock_pin)
            print(f"\n✓ Dock pin (18) with PULL-DOWN:")
            print(f"  Reading: {'HIGH (1)' if dock_with_pull_down else 'LOW (0)'}")
            print(f"  Expected: LOW (0) - pin should be pulled to ground")
            
            # Test pull-up on obstacle pin
            GPIO.setup(self.obstacle_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            obstacle_with_pull_up = GPIO.input(self.obstacle_pin)
            print(f"\n✓ Obstacle pin (21) with PULL-UP:")
            print(f"  Reading: {'HIGH (1)' if obstacle_with_pull_up else 'LOW (0)'}")
            print(f"  Expected: HIGH (1) - pin should be pulled to 3.3V")
            
            return True
            
        except Exception as e:
            print(f"✗ Pull configuration test failed: {e}")
            return False
    
    def continuous_monitor(self, duration: int = 30) -> None:
        """Monitor GPIO pins continuously"""
        print("\n" + "="*60)
        print(f"CONTINUOUS MONITORING ({duration}s)")
        print("="*60)
        print("Press Ctrl+C to stop\n")
        
        try:
            GPIO.setup(self.dock_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.obstacle_pin, GPIO.IN)
            
            start_time = time.time()
            sample_count = 0
            
            while time.time() - start_time < duration:
                dock_state = GPIO.input(self.dock_pin)
                obstacle_state = GPIO.input(self.obstacle_pin)
                
                dock_status = "🟢 DOCKED" if dock_state == GPIO.HIGH else "🔴 NOT DOCKED"
                obstacle_status = "🟢 OBSTACLE" if obstacle_state == GPIO.HIGH else "🔴 CLEAR"
                
                elapsed = time.time() - start_time
                print(f"[{elapsed:6.1f}s] Dock: {dock_status:20} | Obstacle: {obstacle_status}", 
                      end='\r')
                
                sample_count += 1
                time.sleep(0.5)
            
            print(f"\n✓ Monitoring complete ({sample_count} samples collected)")
            
        except KeyboardInterrupt:
            print("\n\n✓ Monitoring stopped by user")
        except Exception as e:
            print(f"✗ Monitoring error: {e}")
    
    def voltage_reference_info(self) -> None:
        """Display GPIO voltage reference information"""
        print("\n" + "="*60)
        print("GPIO VOLTAGE REFERENCE")
        print("="*60)
        
        info = """
Raspberry Pi GPIO Voltage Levels:
  
  HIGH (Logic 1):
    - Range: 2.0V to 3.3V
    - Typical: 3.3V (±0.3V)
    - Safe for RPi: 3.3V native output
  
  LOW (Logic 0):
    - Range: 0V to 0.6V
    - Typical: 0V (±0.3V)
    - Safe for RPi: 0V native output

Common Issues:
  
  ⚠ Using 5V sensors with 3.3V GPIO:
    Solution 1: Voltage divider (R1=10k, R2=10k)
    Solution 2: Level shifter IC
    Solution 3: Check sensor datasheet
  
  ⚠ Unstable/floating readings:
    Solution 1: Add 0.1µF capacitor across sensor
    Solution 2: Enable pull-up or pull-down
    Solution 3: Shorten cable length
  
  ⚠ No response from sensor:
    Check: Power supply to sensor
    Check: Ground connection
    Check: Signal wire connection
        """
        
        print(info)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive diagnostic report"""
        print("\n" + "="*60)
        print("DIAGNOSTIC REPORT")
        print("="*60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "hardware_status": self.test_results,
            "recommendations": [],
            "next_steps": []
        }
        
        # Generate recommendations
        dock_status = self.test_results.get('dock_pin')
        obstacle_status = self.test_results.get('obstacle_pin')
        
        if dock_status == 'ERROR':
            report['recommendations'].append("🔴 Dock pin not responding - Check GPIO 18 connection")
            report['next_steps'].append("1. Verify GPIO 18 is connected to dock sensor")
            report['next_steps'].append("2. Check for loose wires or corrosion")
            report['next_steps'].append("3. Test with multimeter: should read 0V or 3.3V")
        elif dock_status == 'UNSTABLE':
            report['recommendations'].append("⚠ Dock pin is unstable - Add debouncing or filtering")
            report['next_steps'].append("1. Add 100nF capacitor between GPIO 18 and GND")
            report['next_steps'].append("2. Implement software debouncing (3 consecutive reads)")
            report['next_steps'].append("3. Use shielded cable if cable is long")
        elif dock_status == 'ACTIVE':
            report['recommendations'].append("✓ Dock sensor is properly connected and DOCKED")
        elif dock_status == 'INACTIVE':
            report['recommendations'].append("✓ Dock sensor is properly connected (not docked)")
        
        if obstacle_status == 'ERROR':
            report['recommendations'].append("🔴 Obstacle pin not responding - Check GPIO 21 connection")
            report['next_steps'].append("1. Verify GPIO 21 is connected to obstacle sensor")
            report['next_steps'].append("2. Check power supply to sensor")
            report['next_steps'].append("3. Verify signal wire is connected")
        elif obstacle_status == 'UNSTABLE':
            report['recommendations'].append("⚠ Obstacle pin is unstable - Add filtering")
            report['next_steps'].append("1. Add 100nF capacitor between GPIO 21 and GND")
            report['next_steps'].append("2. Check sensor power supply stability")
            report['next_steps'].append("3. Move away from electrical noise sources")
        elif obstacle_status == 'CLEAR':
            report['recommendations'].append("✓ Obstacle sensor is working (path clear)")
        elif obstacle_status == 'OBSTACLE_DETECTED':
            report['recommendations'].append("✓ Obstacle sensor is working (obstacle detected)")
        
        # Print report
        print("\n🔍 STATUS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        if report['next_steps']:
            print("\n📋 NEXT STEPS:")
            for step in report['next_steps']:
                print(f"  {step}")
        
        print("\n✓ Report generated successfully")
        
        return report
    
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        try:
            GPIO.cleanup()
            print("\n✓ GPIO cleaned up")
        except Exception as e:
            print(f"\n✗ GPIO cleanup error: {e}")


def main():
    """Main entry point for diagnostics"""
    print("\n" + "█"*60)
    print("VINNY TACTICAL CORE - GPIO DIAGNOSTICS TOOL")
    print("█"*60)
    
    diag = GPIODiagnostics()
    
    try:
        # Setup GPIO
        if not diag.setup_gpio():
            return
        
        # Run all tests
        diag.test_dock_pin()
        diag.test_obstacle_pin()
        diag.test_pull_configurations()
        diag.voltage_reference_info()
        
        # Offer continuous monitoring
        response = input("\n📡 Run continuous monitoring for 30 seconds? (y/n): ")
        if response.lower() == 'y':
            diag.continuous_monitor(30)
        
        # Generate and display report
        diag.generate_report()
        
        print("\n" + "="*60)
        print("✓ DIAGNOSTICS COMPLETE")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n✗ Diagnostic error: {e}")
    finally:
        diag.cleanup()


if __name__ == "__main__":
    main()
