#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import WrenchStamped
import numpy as np

class ForceSensorProcessor(Node):
    def __init__(self):
        super().__init__('force_sensor_eth_publisher')
        self.nb_zero = 20
        self.zero_buf = []
        self.zero = None
        self.pub = self.create_publisher(WrenchStamped, '/force_sensor_eth', 10)
        self.sub = self.create_subscription(
            WrenchStamped,
            '/bus0/ft_sensor0/ft_sensor_readings/wrench',
            self.callback, 10)
        self.get_logger().info(f'Waiting for {self.nb_zero} readings to compute offset...')

    def callback(self, msg):
        raw = [msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z,
               msg.wrench.torque.x, msg.wrench.torque.y, msg.wrench.torque.z]
        if self.zero is None:
            self.zero_buf.append(raw)
            if len(self.zero_buf) >= self.nb_zero:
                self.zero = np.mean(self.zero_buf, axis=0)
                self.get_logger().info(f'Offset computed: F=[{self.zero[0]:.4f},{self.zero[1]:.4f},{self.zero[2]:.4f}]')
            return
        out = WrenchStamped()
        out.header = msg.header
        out.wrench.force.x  = raw[0] - self.zero[0]
        out.wrench.force.y  = raw[1] - self.zero[1]
        out.wrench.force.z  = raw[2] - self.zero[2]
        out.wrench.torque.x = raw[3] - self.zero[3]
        out.wrench.torque.y = raw[4] - self.zero[4]
        out.wrench.torque.z = raw[5] - self.zero[5]
        self.pub.publish(out)

def main():
    rclpy.init()
    node = ForceSensorProcessor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
