import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2 as cv
import numpy as np
from geometry_msgs.msg import Point

class StereoDistance(Node):
    def __init__(self):
        super().__init__('stereo_distance')

        # Inisialisasi Publisher
        self.target_pub = self.create_publisher(Point, "/asv/target_point", 10)
        self.red_buoy_pub = self.create_publisher(Point, "/asv/red_buoy_info", 10)
        self.orange_buoy_pub = self.create_publisher(Point, "/asv/orange_buoy_info", 10)

        # Inisialisai Subscriber
        self.create_subscription(Image, "/wamv/sensors/cameras/front_left_camera_sensor/image_raw", self.left_cb, 10)
        self.create_subscription(Image, "/wamv/sensors/cameras/front_right_camera_sensor/image_raw", self.right_cb, 10)
        self.create_subscription(CameraInfo, "/wamv/sensors/cameras/front_left_camera_sensor/camera_info", self.cam_info_cb, 10)

        # Variabel Global Class
        self.bridge = CvBridge()
        self.left_img = None
        self.right_img = None

        # Parameter Kamera Stereo
        self.fx = 0.0        # focal length (didapat dari camera_info)
        self.baseline = 0.2  # Jarak antar kamera (meter)
        
        # Parameter navigasi
        self.error = 0.0     # Nilai error heading (pixel)
        self.safe_dist = 3.0 # Jarak aman (meter)

        # Variabel Data Buoy Merah
        self.dist_red = 0.0
        self.forward_dist_red = 0.0
        self.hor_dist_red = 0.0

        # Variabel Data Buoy Oranye
        self.dist_orange = 0.0
        self.forward_dist_orange = 0.0
        self.hor_dist_orange = 0.0

        # kernel untuk operasi morfologi
        self.kernel = np.ones((7, 7), np.uint8)

        self.get_logger().info("Stereo distance node started")
        self.create_timer(0.1, self.process)

    # --- Publish Distance ---
    def target_info(self):
        target, red_info, orange_info = Point(), Point(), Point()

        target.x = self.error

        red_info.x = self.dist_red
        red_info.y = self.forward_dist_red
        red_info.z = self.hor_dist_red

        orange_info.x = self.dist_orange
        orange_info.y = self.forward_dist_orange
        orange_info.z = self.hor_dist_orange
        
        self.target_pub.publish(target)
        self.red_buoy_pub.publish(red_info)
        self.orange_buoy_pub.publish(orange_info)

    # --- Ambil info kamera ---
    def cam_info_cb(self, msg):
        self.fx = msg.k[0]

    # --- Callback kiri ---
    def left_cb(self, msg:Image):
        self.left_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    # --- Callback kanan ---
    def right_cb(self, msg:Image):
        self.right_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    # --- Sorting Objek ---
    def contour_sort(self, contours):
        """
        Mengurutkan kontur dari atas ke bawah berdasarkan koordinat Y (posisi vertikal).
        Menggunakan fungsi bawaan Python sorted() untuk efisiensi komputasi.
        """
        if not contours:
            return [], []
            
        # Mengurutkan berdasarkan elemen indeks ke-1 (nilai Y) dari bounding box
        sorted_contours = sorted(contours, key=lambda c: cv.boundingRect(c)[1], reverse=True)
        
        # Membuat list bounding box dari kontur yang sudah diurutkan
        bounding_rects = [cv.boundingRect(c) for c in sorted_contours]
        
        return sorted_contours, bounding_rects
    
    # --- HELPER MASKING (DRY PRINCIPLE) ---
    def create_color_mask(self, hsv_img, color_type):
        """Membuat mask warna untuk mengurangi repetisi kode."""
        if color_type == 'red':
            mask1 = cv.inRange(hsv_img, np.array([0, 100, 80]), np.array([5, 255, 150]))
            mask2 = cv.inRange(hsv_img, np.array([165, 100, 80]), np.array([179, 255, 150]))
            mask = mask1 | mask2
        elif color_type == 'orange':
            mask = cv.inRange(hsv_img, np.array([10, 100, 100]), np.array([15, 255, 150]))
        else:
            return None
        
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, self.kernel)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, self.kernel)
        return mask
    
    def object_detection(self, boundings_left_red, boundings_right_red, contour_len_red, left_rows, right_rows, color):
        for i in range(contour_len_red):
            xL, yL, wL, hL = boundings_left_red[i]
            xR, yR, wR, hR = boundings_right_red[i]

            cv.rectangle(self.left_img, (xL, yL), (xL+wL, yL+hL), (0, 255, 0), 2)
            cv.rectangle(self.right_img, (xR, yR), (xR+wR, yR+hR), (0, 255, 0), 2)

            disparity = (xL + (wL/2)) - (xR + (wR/2))
            distance = (self.fx * self.baseline) / abs(disparity)

            self.get_logger().info(f"fx={self.fx:.2f}, disp={disparity:.2f}, dist={distance:.2f}")
            cv.putText(self.left_img,
                        f"Dist: {distance:.2f} m",
                        (xL, yL-10),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 255), 2)
            
            left_center = wL // 2 + xL
            right_center = wR // 2 + xR

            img_center_x = self.left_img.shape[1] / 2.0
            dx = left_center - img_center_x

            # Kalkulasi Trigonometri (Sudut dari titik tengah)
            object_angle = np.arctan(dx / self.fx)
            forward_distance = distance * np.cos(object_angle)  
            hor_distance = distance * np.sin(object_angle)  
            
            cv.line(self.left_img, (left_center, 0), (left_center, left_rows), (255, 255, 0), 2)
            cv.line(self.right_img, (right_center, 0), (right_center, right_rows), (255, 255, 0), 2)

            # Hanya simpan objek terdekat (index 0)
            if i == 0:
                if color == "red":
                    self.dist_red = distance
                    self.forward_dist_red = forward_distance
                    self.hor_dist_red = hor_distance

                    print(f'the red angle = {object_angle}')
                    print(f'red forward distance = {forward_distance}')
                    print(f'hor dist red= {hor_distance}')
                
                elif color == "orange":
                    self.dist_orange = distance
                    self.forward_dist_orange = forward_distance
                    self.hor_dist_orange = hor_distance

                    print(f'the orange angle = {object_angle}')
                    print(f'orange forward distance = {forward_distance}')
                    print(f'hor dist orange= {hor_distance}')

    # --- Proses utama ---
    def process(self):
        if self.left_img is None or self.right_img is None or self.fx == 0.0:
            print("GAMBAR TIDAK TERDETEKSI")
            return
        
        left_rows = self.left_img.shape[0]
        right_rows = self.right_img.shape[0]

        # Mask warna merah (buat deteksi buoy)
        hsv_left = cv.cvtColor(self.left_img, cv.COLOR_BGR2HSV)
        hsv_right = cv.cvtColor(self.right_img, cv.COLOR_BGR2HSV)

        # Masking 
        mask_left_red = self.create_color_mask(hsv_left, 'red')
        mask_right_red = self.create_color_mask(hsv_right, 'red')
        mask_left_orange = self.create_color_mask(hsv_left, 'orange')
        mask_right_orange = self.create_color_mask(hsv_right, 'orange')

        # Cari dan urutkan kontur merah
        contours_left_red, _ = cv.findContours(mask_left_red, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_right_red, _ = cv.findContours(mask_right_red, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_left_red, boundings_left_red = self.contour_sort(list(contours_left_red))
        contours_right_red, boundings_right_red = self.contour_sort(list(contours_right_red))
        
        # Cari dan urutkan kontur oranye
        contours_left_orange, _ = cv.findContours(mask_left_orange, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_right_orange, _ = cv.findContours(mask_right_orange, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_left_orange, boundings_left_orange = self.contour_sort(list(contours_left_orange))
        contours_right_orange, boundings_right_orange = self.contour_sort(list(contours_right_orange))
        
        #--- Stereo matching ---
        contour_len_red = min(len(contours_left_red), len(contours_right_red))
        contour_len_orange = min(len(contours_left_orange), len(contours_right_orange))

        if (contours_left_red and contours_right_red) or (contours_left_orange and contours_right_orange):
            
            # Deteksi dan estimasi buoy merah
            self.object_detection(boundings_left_red, boundings_right_red, contour_len_red, left_rows, right_rows, color="red")
            # Deteksi dan estimasi buoy orange
            self.object_detection(boundings_left_orange, boundings_right_orange, contour_len_orange, left_rows, right_rows, color="orange")

            if contour_len_red > 0 and contour_len_orange > 0:
                xL_red, yL_red, wL_red, hL_red = boundings_left_red[0]
                xL_org, yL_org, wL_org, hL_org = boundings_left_orange[0]
                xR_red, yR_red, wR_red, hR_red = boundings_right_red[0] 
                xR_org, yR_org, wR_org, hR_org = boundings_right_orange[0]

                xRed = wL_red // 2 + xL_red
                xOrange = wL_org // 2 + xL_org

                yRed = hL_red // 2 + yL_red
                yOrange = hL_org // 2 + yL_org

                # Syarat kondisi valid gate/jalur
                if abs(xOrange - xRed) > 100 and (xOrange >= xRed) and self.dist_red > self.safe_dist and self.dist_orange > self.safe_dist and xL_red > 100 and xR_red < (self.left_img.shape[1] - 100):
                    xCenter = ((xRed) + (xOrange)) // 2
                    yCenter = ((yRed) + (yOrange)) // 2

                    xCenter = (xRed + xOrange) // 2
                    yCenter = ((yRed) + (yOrange)) // 2
                    
                    # Target pixel error (Tengah target dikurangi tengah kamera)
                    img_center_x = self.left_img.shape[1] // 2
                    self.error = float(xCenter - img_center_x)

                    cv.line(img=self.left_img, pt1=(wL_red // 2 + xL_red, hL_red // 2 + yL_red), pt2=(wL_org // 2 + xL_org, hL_org // 2 + yL_org), color=(255, 0, 0), thickness=2)
                    cv.line(img=self.right_img, pt1=(wR_red // 2 + xR_red, hR_red // 2 + yR_red), pt2=(wR_org // 2 + xR_org, hR_org // 2 + yR_org), color=(255, 0, 0), thickness=2)
                    cv.circle(img=self.left_img, center=(xCenter, yCenter), radius=5, color=(0,255,0), thickness=-2)

            elif contour_len_red > 0 and contour_len_orange == 0:
                # HANYA MERAH
                self.dist_orange = self.forward_dist_orange = self.hor_dist_orange = 0.0
                self.error = 0.0
                self.get_logger().warning(f"STATUS: HANYA MERAH. Jarak Z: {self.dist_red:.2f}m")

            elif contour_len_orange > 0 and contour_len_red == 0:
                # HANYA ORANYE
                self.dist_red = self.forward_dist_red = self.hor_dist_red = 0.0
                self.error = 0.0
                self.get_logger().warning(f"STATUS: HANYA ORANYE. Jarak Z: {self.dist_orange:.2f}m")

        else:
            # TIDAK ADA YANG TERDETEKSI
            self.dist_red = self.forward_dist_red = self.hor_dist_red = 0.0
            self.dist_orange = self.forward_dist_orange = self.hor_dist_orange = 0.0
            self.error = 0.0
            self.get_logger().error("STATUS: TIDAK ADA BUOY TERDETEKSI")
        
        # Publish data
        self.target_info()
        
        print(f'error: {self.error}')
        
        cv.line(img=self.left_img, pt1=(self.left_img.shape[1] // 2, 0), pt2=(self.left_img.shape[1] // 2, self.left_img.shape[0]), color=(0,0,255), thickness=2)

        combine = np.vstack((self.left_img, self.right_img))
        cv.imshow("red mask", mask_left_red)
        cv.imshow("orange mask", mask_left_orange)
        cv.imshow("stereo result", combine)
        cv.waitKey(1)

def main():
    rclpy.init()
    node = StereoDistance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()