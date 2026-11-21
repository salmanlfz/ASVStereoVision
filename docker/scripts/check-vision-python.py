#!/usr/bin/env python3
"""Check the NumPy/OpenCV/cv_bridge ABI with an actual image conversion."""
import numpy as np
import cv2
from cv_bridge import CvBridge

assert np.__version__.split('.')[0] == '1', np.__version__
image = np.zeros((2, 3, 3), dtype=np.uint8)
image[:, :] = (10, 20, 30)
bridge = CvBridge()
message = bridge.cv2_to_imgmsg(image, encoding='bgr8')
rgb = bridge.imgmsg_to_cv2(message, desired_encoding='rgb8')
assert np.array_equal(rgb, cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
print(f'PASS: NumPy {np.__version__} ({np.__file__}), '
      f'OpenCV {cv2.__version__} ({cv2.__file__}), cv_bridge BGR→RGB conversion')
