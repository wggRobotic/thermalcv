#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np
import os # Hilfreich, um zu prüfen, ob das Testbild existiert

class RedObjectDetectorNode(Node):
    def __init__(self):
        super().__init__('red_object_detector')
        
        # Publisher bleibt für beide Varianten gleich, damit du das Ergebnis sehen kannst
        self.publisher = self.create_publisher(
            CompressedImage,
            '/image_out/compressed',
            10
        )
        
        # --- VARIANTE A: Normaler ROS 2 Betrieb (Standard) ---
        self.subscription = self.create_subscription(
            CompressedImage,
            '/image_in/compressed',
            self.image_callback,
            10
        )
        self.test_timer = None

        # --- VARIANTE B: Testbild-Modus (Zum Testen einkommentieren, Variante A auskommentieren) ---
        self.subscription = None
        # Ruft die Methode 10-mal pro Sekunde (0.1s Intervall) mit einer Dummy-Nachricht auf
        self.test_timer = self.create_timer(0.1, lambda: self.image_callback(None))
        # Pfad zu deinem Testbild auf der Festplatte anpassen:
        self.test_image_path = '/home/corvus/Downloads/image.png'
        
        self.get_logger().info('Red Object Detector Node wurde gestartet.')

    def image_callback(self, msg):
        try:
            # --- BILD-QUELLE AUSWÄHLEN ---
            if self.test_timer is not None:
                # Modus: Testbild laden
                if not os.path.exists(self.test_image_path):
                    self.get_logger().error(f'Testbild nicht gefunden unter: {self.test_image_path}')
                    return
                cv_image = cv2.imread(self.test_image_path)
            else:
                # Modus: Live-Bilder von ROS 2 verarbeiten
                np_arr = np.frombuffer(msg.data, np.uint8)
                cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if cv_image is None:
                self.get_logger().error('Bild konnte nicht geladen/dekodiert werden.')
                return

            # --- AB HIER BLEIBT DER CODE IDENTISCH ---
            hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
            mask = mask1 + mask2

            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 500:
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 0, 0), 8)
                    cv2.putText(cv_image, 'Rote Flaeche', (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Ergebnis auf das Output-Topic publishen
            success, encoded_image = cv2.imencode('.jpg', cv_image)
            if success:
                out_msg = CompressedImage()
                # Falls msg None ist (im Testmodus), füllen wir den Header minimal selbst
                if msg is not None:
                    out_msg.header = msg.header
                else:
                    out_msg.header.stamp = self.get_clock().now().to_msg()
                    out_msg.header.frame_id = "test_frame"
                    
                out_msg.format = "jpeg"
                out_msg.data = encoded_image.tobytes()
                self.publisher.publish(out_msg)
                
        except Exception as e:
            self.get_logger().error(f'Fehler bei der Bildverarbeitung: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = RedObjectDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()