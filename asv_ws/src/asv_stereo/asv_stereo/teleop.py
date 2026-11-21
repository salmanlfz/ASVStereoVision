import sys
import termios
import tty
import select
import rclpy
import os
import time
from rclpy.node import Node
from std_msgs.msg import Float64

MSG = """
---------------------------
Kapal Teleop Control
---------------------------
↑ : Forward
← ↓ →: Turn Left / Backward / Turn Right
Release key = Auto Stop
CTRL-C to quit
---------------------------
"""


class KapalTeleop(Node):
    def __init__(self):
        super().__init__("kapal_teleop")

        # Speed settings
        self.FORWARD_SPEED = 1000.0  # Thrust saat maju
        self.TURN_SPEED = 750.0      # Thrust saat belok

        # Speeds Sekarang
        self.left_speed = 0.0
        self.right_speed = 0.0

        # Inisialisasi Publishers
        self.pub_left = self.create_publisher(Float64, "/wamv/thrusters/left/thrust", 10)
        self.pub_right = self.create_publisher(Float64, "/wamv/thrusters/right/thrust", 10)

        # Timer untuk publish (20 Hz)
        self.timer = self.create_timer(0.05, self.publish_thrust)

        # Terminal settings
        self.settings = termios.tcgetattr(sys.stdin)

        print(MSG)
        self.get_logger().info("Kapal teleop ready")

    def publish_thrust(self):
        """Publish nilai Thrust"""
        self.pub_left.publish(Float64(data=self.left_speed))
        self.pub_right.publish(Float64(data=self.right_speed))

    def get_key(self, timeout=0.05):
        """
        Mengambil keyboard input dengan batas waktu
        Returns None jika tidak ada tombol ditekan (key released)
        """
        tty.setraw(sys.stdin.fileno())
        # Mengecek jika terdapat input dalam batas waktu
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
            # Handle jika tombol arrow ditekan (arrow keys)
            # Arrow keys send 3 chars: ESC [ A/B/C/D
            if key == '\x1b':
                next1 = sys.stdin.read(1)
                next2 = sys.stdin.read(1)
                key = key + next1 + next2
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            return key
        else:
            # No input = key released
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            return None

    def run(self):
        """Main teleop loop"""
        try:
            while rclpy.ok():
                # Mendapatkan tombol yang ditekan dalam batas waktu
                key = self.get_key(timeout=0.05)

                if key is None:
                    # Tidak ada tombol ditekan = STOP
                    self.left_speed = 0.0
                    self.right_speed = 0.0
                elif key == '\x1b[A':  # UP Arrow - Maju
                    self.left_speed = self.FORWARD_SPEED
                    self.right_speed = self.FORWARD_SPEED
                    print(f'\r↑ Forward ({self.FORWARD_SPEED:.0f}) ', end='', flush=True)
                elif key == '\x1b[B':  # DOWN Arrow - Mundur
                    self.left_speed = -self.FORWARD_SPEED
                    self.right_speed = -self.FORWARD_SPEED
                    print(f'\r↓ Backward ({self.FORWARD_SPEED:.0f}) ', end='', flush=True)
                elif key == '\x1b[C':  # RIGHT Arrow - Belok Kanan
                    self.left_speed = self.TURN_SPEED
                    self.right_speed = -self.TURN_SPEED
                    print(f'\r→ Turn Right ({self.TURN_SPEED:.0f}) ', end='', flush=True)
                elif key == '\x1b[D':  # LEFT Arrow - Belok Kiri
                    self.left_speed = -self.TURN_SPEED
                    self.right_speed = self.TURN_SPEED
                    print(f'\r← Turn Left ({self.TURN_SPEED:.0f}) ', end='', flush=True)
                elif key == '\x03':  # CTRL-C - keluar dari teleop
                    print('\n\nShutting down...')
                    break

                # Spin ROS
                rclpy.spin_once(self, timeout_sec=0)

        except Exception as e:
            self.get_logger().error(f'Error: {e}')

        finally:
            # Stop thrusters
            self.left_speed = 0.0
            self.right_speed = 0.0
            self.publish_thrust()

            # Restore terminal
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print('\nTeleop stopped. Boat stopped.')

def main():
    rclpy.init()
    node = KapalTeleop()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()