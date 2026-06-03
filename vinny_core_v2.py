"""
Vinny Tactical Core v2 - Enhanced Robot Control System
Adds obstacle detection, hysteresis power logic, and autonomous speech
"""

import serial
import smbus2
import ADS1x15
import threading
import time
import logging
import json
from typing import Tuple, Dict, Optional
from enum import Enum
import RPi.GPIO as GPIO
from config import DOCK_PIN, SERIAL_PORT, OBSTACLE_PIN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
VOLTAGE_CRITICAL_THRESHOLD = 11.2      # Volts, triggers return-to-dock
VOLTAGE_RECOVERY_THRESHOLD = 11.7      # Hysteresis upper bound
ADC_VOLTAGE_MULTIPLIER = 0.000125      # 4.096V / 32767 counts
ADC_GAIN_FACTOR = 4.0
MONITOR_INTERVAL = 0.5                 # Seconds between checks
ADC_CHANNEL = 0
ADC_GAIN = 1
SAFE_PARK_SPEED = 25                   # Motor speed for safe parking
SAFE_PARK_DURATION = 2                 # Seconds


class SystemState(Enum):
    """Robot system states"""
    PATROL = "PATROL"
    AVOIDING_OBSTACLE = "AVOIDING_OBSTACLE"
    RETURNING_TO_DOCK = "RETURNING_TO_DOCK"
    DOCKING_SUCCESS = "DOCKING_SUCCESS"
    SAFE_PARK = "SAFE_PARK"


class VinnyTacticalCore:
    """Enhanced robot core control system with obstacle detection and autonomy"""
    
    def __init__(self):
        """Initialize robot systems and start monitoring"""
        self.system_state = SystemState.PATROL.value
        self.current_voltage = 12.6
        self._state_lock = threading.Lock()
        self._telemetry_lock = threading.Lock()
        self.running = True
        
        # Telemetry buffer
        self.telemetry_buffer = []
        self.max_buffer_size = 100
        
        # Obstacle tracking
        self.obstacle_detected_count = 0
        self.last_obstacle_time = 0
        
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
            GPIO.setup(OBSTACLE_PIN, GPIO.IN)
            logger.info(f"GPIO pins configured - Dock: {DOCK_PIN}, Obstacle: {OBSTACLE_PIN}")
            
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
                logger.info(f"State transition: {self.system_state} → {new_state}")
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
            if state == SystemState.DOCKING_SUCCESS.value:
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
            logger.error(f"GPIO dock sensor read error: {e}")
            return False

    def check_obstacle_sensor(self) -> bool:
        """
        Check if obstacle is detected
        
        Returns:
            True if obstacle detected (sensor HIGH), False otherwise
        """
        try:
            is_obstacle = GPIO.input(OBSTACLE_PIN) == GPIO.HIGH
            if is_obstacle:
                self.obstacle_detected_count += 1
                self.last_obstacle_time = time.time()
            return is_obstacle
        except Exception as e:
            logger.error(f"GPIO obstacle sensor read error: {e}")
            return False

    def speak_autonomously(self, message: str) -> None:
        """
        Output autonomous speech message
        
        Args:
            message: Message for robot to speak
        """
        output = f"[🤖 VINNY]: {message}"
        print(output)
        logger.info(f"SPEECH: {message}")

    def get_telemetry(self) -> Dict:
        """
        Get current system telemetry
        
        Returns:
            Dictionary containing system state and voltage
        """
        return {
            "state": self.get_state(),
            "voltage": round(self.current_voltage, 2),
            "timestamp": time.time(),
            "obstacles_detected": self.obstacle_detected_count
        }

    def log_telemetry(self) -> None:
        """
        Log current telemetry data
        """
        try:
            telemetry = self.get_telemetry()
            
            # Add to buffer
            with self._telemetry_lock:
                self.telemetry_buffer.append(telemetry)
                if len(self.telemetry_buffer) > self.max_buffer_size:
                    self.telemetry_buffer.pop(0)
            
            # Log to console
            print(f"[📡 TELEMETRY]: {json.dumps(telemetry)}")
            logger.debug(f"Telemetry: {json.dumps(telemetry)}")
            
        except Exception as e:
            logger.error(f"Telemetry logging error: {e}")

    def perform_safe_park(self) -> None:
        """
        Perform safe parking procedure
        Gradually slows robot and stops safely
        """
        try:
            self.set_state(SystemState.SAFE_PARK.value)
            self.speak_autonomously("Initiating Safe Park.")
            
            # Gradual deceleration
            self.apply_motor_matrix(SAFE_PARK_SPEED, SAFE_PARK_SPEED)
            time.sleep(SAFE_PARK_DURATION)
            self.apply_motor_matrix(0, 0)
            
            logger.info("Safe park completed")
            
        except Exception as e:
            logger.error(f"Safe park error: {e}")
            self.apply_motor_matrix(0, 0)  # Emergency stop

    def handle_obstacle_avoidance(self) -> None:
        """
        Handle obstacle detection and avoidance
        """
        try:
            if self.get_state() == SystemState.PATROL.value:
                self.set_state(SystemState.AVOIDING_OBSTACLE.value)
                self.apply_motor_matrix(0, 0)
                self.speak_autonomously("Obstacle detected. Stopping.")
                time.sleep(1)
                # Could add evasive maneuver here
                self.set_state(SystemState.PATROL.value)
                
        except Exception as e:
            logger.error(f"Obstacle avoidance error: {e}")

    def handle_voltage_critical(self) -> None:
        """
        Handle critical low voltage condition
        """
        try:
            if self.get_state() == SystemState.PATROL.value:
                self.set_state(SystemState.RETURNING_TO_DOCK.value)
                self.perform_safe_park()
                logger.warning(f"Low voltage detected: {self.current_voltage:.1f}V")
                
        except Exception as e:
            logger.error(f"Voltage critical handling error: {e}")

    def handle_voltage_recovery(self) -> None:
        """
        Handle voltage recovery (hysteresis logic)
        """
        try:
            if self.get_state() == SystemState.RETURNING_TO_DOCK.value:
                self.set_state(SystemState.PATROL.value)
                self.speak_autonomously("Voltage recovered. Resuming patrol.")
                logger.info(f"Voltage recovered: {self.current_voltage:.1f}V")
                
        except Exception as e:
            logger.error(f"Voltage recovery handling error: {e}")

    def handle_dock_detected(self) -> None:
        """
        Handle dock sensor detection
        """
        try:
            if self.get_state() != SystemState.DOCKING_SUCCESS.value:
                self.set_state(SystemState.DOCKING_SUCCESS.value)
                self.apply_motor_matrix(0, 0)
                self.speak_autonomously("Dock detected. Beginning charge cycle.")
                logger.info("Robot successfully docked")
                
        except Exception as e:
            logger.error(f"Dock handling error: {e}")

    def run_background_tasks(self) -> None:
        """
        Background monitoring loop - runs in separate thread
        Monitors voltage, dock status, and obstacles
        """
        logger.info("Background task loop started")
        
        while self.running:
            try:
                # 1. Read and update voltage
                self.current_voltage = self.read_voltage()
                logger.debug(f"Battery voltage: {self.current_voltage:.1f}V")
                
                state = self.get_state()
                
                # 2. Voltage-based state machine with hysteresis
                if (self.current_voltage < VOLTAGE_CRITICAL_THRESHOLD 
                    and state != SystemState.DOCKING_SUCCESS.value):
                    self.handle_voltage_critical()
                
                elif (self.current_voltage > VOLTAGE_RECOVERY_THRESHOLD 
                      and state == SystemState.RETURNING_TO_DOCK.value):
                    self.handle_voltage_recovery()
                
                # 3. Obstacle detection
                if self.check_obstacle_sensor():
                    self.handle_obstacle_avoidance()
                
                # 4. Dock sensor check
                if self.check_dock_sensor():
                    self.handle_dock_detected()
                
                # 5. Log telemetry
                self.log_telemetry()
                
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
