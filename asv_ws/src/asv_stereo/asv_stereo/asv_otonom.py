import rclpy
from rclpy.node import Node 
from std_msgs.msg import Float64
from geometry_msgs.msg import Point

class otonom(Node):
    def __init__(self):
        super().__init__("kapal_otonom")
        
        # Inisialisasi Subsriber
        self.create_subscription(Point, "/asv/target_point", self.target_info, 10)
        self.create_subscription(Point, "/asv/red_buoy_info", self.red_buoy_info, 10)
        self.create_subscription(Point, "/asv/orange_buoy_info", self.orange_buoy_info, 10)

        self.left_thrust = self.create_publisher(Float64, "/wamv/thrusters/left/thrust", 10)
        self.right_thrust = self.create_publisher(Float64, "/wamv/thrusters/right/thrust", 10)

        self.error = 0.0
        self.safe_dist = 3.0
        self.safe_pixel = 150
        self.safe_lat_dist = 4.0

        #RED BUOY DISTANCE
        self.dist_red = 0.0
        self.forward_dist_red = 0.0
        self.hor_dist_red = 0.0
        
        # ORANGE BUOY DISTANCE
        self.dist_orange = 0.0
        self.forward_dist_orange = 0.0
        self.hor_dist_orange = 0.0

        self.left_speed = 0.0
        self.right_speed = 0.0
        
        self.FORWARD_SPEED = 900.0   # Thrust saat maju
        self.TURN_SPEED = 300.0      # Thrust saat belok

        self.create_timer(0.1, self.autonomous)

    def target_info(self, msg:Point):
        self.error = msg.x

    def red_buoy_info(self, msg:Point):
        self.dist_red = msg.x
        self.forward_dist_red = msg.y
        self.hor_dist_red = abs(msg.z)

    def orange_buoy_info(self, msg:Point):
        self.dist_orange = msg.x
        self.forward_dist_orange = msg.y
        self.hor_dist_orange = abs(msg.z)

    def thrust_pub(self):
        self.left_thrust.publish(Float64(data=self.left_speed))
        self.right_thrust.publish(Float64(data=self.right_speed))

    def autonomous(self):
        if self.error > self.safe_pixel or (self.dist_red != 0.0 and self.dist_orange == 0.0):
            self.get_logger().info(f'NGANANNNNNNN')
            
            self.left_speed = self.TURN_SPEED
            self.right_speed = -self.TURN_SPEED

            if (self.forward_dist_red > 0 and self.forward_dist_red < self.safe_dist):
                self.left_speed -= self.TURN_SPEED / 3
                self.right_speed += self.TURN_SPEED / 3
            
        elif self.error < -self.safe_pixel or (self.dist_red == 0.0 and self.dist_orange != 0.0):
            self.get_logger().info(f'NGIRIIIIIIII')
            
            self.left_speed = -self.TURN_SPEED
            self.right_speed = self.TURN_SPEED

            if (self.forward_dist_orange > 0 and self.forward_dist_orange < self.safe_dist):
                self.left_speed -= self.TURN_SPEED / 3
                self.right_speed += self.TURN_SPEED / 3
        
        elif self.error <= self.safe_pixel and self.error >= -self.safe_pixel:
            self.get_logger().info(f'MAJUUUUUUUUUU')

            self.left_speed = self.FORWARD_SPEED
            self.right_speed = self.FORWARD_SPEED

            # buoy_distance = self.dist_red-self.dist_orange

            if self.hor_dist_red < self.safe_lat_dist:
                self.left_speed += self.TURN_SPEED
                self.right_speed -= self.TURN_SPEED
            elif self.hor_dist_orange < self.safe_lat_dist:
                self.left_speed -= self.TURN_SPEED
                self.right_speed += self.TURN_SPEED
        
        print(f'hor dist red= {self.hor_dist_red}')
        print(f'hor dist orange= {self.hor_dist_orange}')
    
        self.get_logger().info(f'error: {self.error}, dist_red: {self.dist_red}, dist_orange: {self.dist_orange}')
        self.thrust_pub()    

def main():
    rclpy.init()

    kapal = otonom()

    rclpy.spin(kapal)

    rclpy.shutdown()

if __name__ == "__main__":
    main()