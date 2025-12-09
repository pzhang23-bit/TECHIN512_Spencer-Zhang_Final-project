# AXDL345+ NEOPIXEL: Pickup the device-blue,game over-red.
import time
import board
import neopixel
import adafruit_adxl34x

class AccelMonitor:
    """Monitor ADXL345 accelerometer and control NeoPixel based on pickup"""
    
    def __init__(self, i2c, neopixel_pin=board.D10, num_pixels=1, brightness=0.3): #self,i2c-main.py, call itself
        """
        Initialize accelerometer and NeoPixel
        
        Args:
            i2c: Shared I2C bus instance
            neopixel_pin: GPIO pin for NeoPixel (default: D10)
            num_pixels: Number of pixels in strip (default: 1)
            brightness: Brightness level 0.0-1.0 (default: 0.3)
        """
        self.num_pixels = num_pixels
        
        # Setup NeoPixel
        self.pixels = neopixel.NeoPixel(neopixel_pin, num_pixels, 
                                       brightness=brightness, 
                                       auto_write=False)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        
        # Setup ADXL345 Accelerometer using shared I2C
        try:
            # Try default address first (0x53)
            try:
                self.accel = adafruit_adxl34x.ADXL345(i2c)
                print("ADXL345 found at address 0x53")
            except:
                # Try alternate address (0x1D)
                self.accel = adafruit_adxl34x.ADXL345(i2c, address=0x1D)
                print("ADXL345 found at address 0x1D")
            
            self.has_accel = True
            print("ADXL345 Accelerometer initialized")
        except Exception as e:
            print(f"No accelerometer found: {e}")
            self.has_accel = False
        
        self.is_picked_up = False
        self.manual_override = False  # For game over red light
        self.last_pickup_time = 1.0  # Track last pickup time
        self.hold_duration = 2.0  # Hold light for 2 seconds after pickup (可以调整)
    
    def check_pickup(self):
        """Check if device is picked up based on acceleration"""
        if not self.has_accel:
            return False
        
        try:
            x, y, z = self.accel.acceleration
            
            # Calculate total acceleration magnitude
            total = (x**2 + y**2 + z**2) ** 0.5
            
            # Lower threshold for easier triggering
            if total > 8 or z > 8: 
                return True
            return False
            
        except:
            return False
    
    def update(self):
        """Update NeoPixel based on pickup state (call this frequently)"""
        
        # Don't update if manual override is active (e.g., game over)
        if self.manual_override:
            return
        
        picked_up = self.check_pickup()
        current_time = time.monotonic()
        
        # If picked up, update last pickup time
        if picked_up:
            self.last_pickup_time = current_time
        
        # Keep light on if within hold duration
        should_be_on = (current_time - self.last_pickup_time) < self.hold_duration
        
        # Only update if state changed (reduces unnecessary updates)
        if should_be_on != self.is_picked_up:
            self.is_picked_up = should_be_on
            
            if should_be_on:
                # Device picked up or recently picked up - blue light
                self.pixels.fill((0, 0, 100))
                self.pixels.show()
            else:
                # Device at rest - turn off
                self.pixels.fill((0, 0, 0))
                self.pixels.show()
    
    def set_red(self):
        """Set red light (for game over) - overrides pickup detection"""
        self.manual_override = True
        self.pixels.fill((255, 0, 0))
        self.pixels.show()
    
    def clear_override(self):
        """Clear manual override and return to normal pickup detection"""
        self.manual_override = False
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
    
    def off(self):
        """Turn off all lights"""
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

# Standalone Test
if __name__ == "__main__":
    import board
    import busio
    
    print("=== ADXL345 Accelerometer Monitor Test ===")
    
    # Create I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
    
    monitor = AccelMonitor(i2c, neopixel_pin=board.D10, num_pixels=1)
    
    print("Monitoring... Pick up the device to see blue light")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            monitor.update()
            time.sleep(0.05)  # Check 20 times per second
    except KeyboardInterrupt:
        print("\nStopping...")
        monitor.off()
