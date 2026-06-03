"""
Vinny Tactical Core - Robot Control System
Manages motor control, power monitoring, and docking behavior
"""

import serial
import smbus2
import ADS1x15
import threading
import time
import logging
import RPi.GPIO as GPIO
from typing import Tuple
from config import DOCK_PIN, SERIAL_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
VOLTAGE_CRITICAL_THRESHOLD = 11.2
ADC_VOLTAGE_MULTIPLIER = 0.000125  # 4.096V / 32767 counts
ADC_GAIN_FACTOR = 4.0
MONITOR_INTERVAL = 0.5
ADC_CHANNEL = 0
ADC_GAIN = 1


class VinnyTacticalCore:
    """Robot core control system with motor and power management"""
    
    def __init__(self):
        """Initialize robot systems and start monitoring"""
        self.system_state = "PATROL"
        self.current_voltage = 12.6
        self._state_lock = threading.Lock()
        self.running = True
        
        try:
            # Initialize serial communication
            self.ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
            logger.info(f"Serial port {SERIAL_PORT} opened successfully")
            
            # Initialize ADC
            self.adc = ADS1x15.ADS1115()
            logger.info("ADC initialized")
            
            # Initialize GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(DOCK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            logger.info(f"Dock pin {DOCK_PIN} configured")
            
            # Start background monitoring thread
            self.monitor_thread = threading.Thread(
                target=self.run_background_tasks,
                daemon=True,
                name="MonitorThread"
            )
            self.monitor_thread.start()
            logger.info("Background monitoring thread started")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.cleanup()
            raise

    def get_state(self) -> str:
        """Thread-safe getter for system state"""
        with self._state_lock:
            return self.system_state
    
    def set_state(self, new_state: str) -> None:
        """Thread-safe setter for system state"""
        with self._state_lock:
            if self.system_state != new_state:
                logger.info(f"State transition: {self.system_state} -> {new_state}")
                self.system_state = new_state

    def apply_motor_matrix(self, left: int, right: int) -> None:
        """
        Apply motor commands with state-based safety checks
        
        Args:
            left: Left motor speed (-128 to 127)
            right: Right motor speed (-128 to 127)
        """
        try:
            state = self.get_state()
            
            # Safety: Stop motors if docked
            if state == "DOCKING_SUCCESS":
                left, right = 0, 0
            
            # Clamp values to valid range
            left = max(-128, min(127, left))
            right = max(-128, min(127, right))
            
            # Motor command format: [header_left, flags_left, speed_left, 
            #                        header_right, flags_right, speed_right]
            command = bytes([128, 0, abs(left), 128, 4, abs(right)])
            self.ser.write(command)
            logger.debug(f"Motor command sent: L={left}, R={right}")
            
        except serial.SerialException as e:
            logger.error(f"Serial error sending motor command: {e}")
        except Exception as e:
            logger.error(f"Motor command error: {e}")

    def read_voltage(self) -> float:
        """
        Read battery voltage from ADC
        
        Returns:
            Battery voltage in volts
        """
        try:
            raw = self.adc.read_adc(ADC_CHANNEL, gain=ADC_GAIN)
            voltage = (raw * ADC_VOLTAGE_MULTIPLIER) * ADC_GAIN_FACTOR
            return voltage
        except Exception as e:
            logger.error(f"ADC read error: {e}")
            return self.current_voltage  # Return last known value

    def check_dock_sensor(self) -> bool:
        """
        Check if robot is docked
        
        Returns:
            True if dock pin is HIGH (docked), False otherwise
        """
        try:
            return GPIO.input(DOCK_PIN) == GPIO.HIGH
        except Exception as e:
            logger.error(f"GPIO read error: {e}")
            return False

    def run_background_tasks(self) -> None:
        """
        Background monitoring loop - runs in separate thread
        Monitors voltage and dock status
        """
        logger.info("Background task loop started")
        
        while self.running:
            try:
                # Read and update voltage
                self.current_voltage = self.read_voltage()
                logger.debug(f"Battery voltage: {self.current_voltage:.1f}V")
                
                state = self.get_state()
                
                # Battery critical check
                if (self.current_voltage < VOLTAGE_CRITICAL_THRESHOLD 
                    and state != "DOCKING_SUCCESS"):
                    self.set_state("RETURNING_TO_DOCK")
                
                # Dock sensor check
                if self.check_dock_sensor():
                    self.set_state("DOCKING_SUCCESS")
                    self.apply_motor_matrix(0, 0)
                    logger.info("Docking successful - motors stopped")
                
                time.sleep(MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Background task error: {e}")
                time.sleep(MONITOR_INTERVAL)

    def cleanup(self) -> None:
        """Clean up resources before shutdown"""
        logger.info("Cleaning up resources...")
        
        self.running = False
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            logger.info("Serial port closed")
        
        try:
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except Exception as e:
            logger.error(f"GPIO cleanup error: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


def main():
    """Main entry point"""
    try:
        vinny = VinnyTacticalCore()
        print("✓ Vinny Tactical Core Online.")
        logger.info("System ready")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if 'vinny' in locals():
            vinny.cleanup()
        logger.info("System shutdown complete")


if __name__ == "__main__":
    main()
