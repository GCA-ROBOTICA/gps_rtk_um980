import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

class TrazadorRuta(Node):
    def __init__(self):
        super().__init__('trazador_ruta_node')
        # Suscribirse al GPS
        self.subscription = self.create_subscription(NavSatFix, '/fix', self.listener_callback, 10)
        # Publicar la Ruta
        self.path_pub = self.create_publisher(Path, '/ruta_seguida', 10)
        self.path = Path()
        self.path.header.frame_id = 'map' # O 'gps' dependiendo de tu config

    def listener_callback(self, msg):
        # Solo guardamos puntos si el GPS tiene señal (status >= 0)
        if msg.status.status >= 0:
            pose = PoseStamped()
            pose.header = msg.header
            # Usamos lat/lon como x/y para visualizar rápido en 2D
            pose.pose.position.x = msg.latitude
            pose.pose.position.y = msg.longitude
            pose.pose.position.z = 0.0
            
            self.path.poses.append(pose)
            self.path.header.stamp = self.get_clock().now().to_msg()
            self.path_pub.publish(self.path)

def main(args=None):
    rclpy.init(args=args)
    node = TrazadorRuta()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()