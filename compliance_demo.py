#!/usr/bin/env python3
"""
Compliance demo — publishes current pose as target frame continuously
so the robot doesn't spring back to a fixed position.
This makes it feel more like freedrive.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, WrenchStamped

class ComplianceDemo(Node):
    def __init__(self):
        super().__init__('compliance_demo')
        self.pub_frame = self.create_publisher(PoseStamped, '/target_frame', 10)
        self.pub_wrench = self.create_publisher(WrenchStamped, '/target_wrench', 10)
        self.sub = self.create_subscription(
            PoseStamped, '/cartesian_compliance_controller/current_pose',
            self.pose_cb, 10)
        self.timer = self.create_timer(0.02, self.publish_wrench)  # 50Hz
        self.last_pose = None
        self.get_logger().info('Compliance demo started — push the robot!')

    def pose_cb(self, msg):
        # Update target to current pose — robot doesn't spring back
        self.last_pose = msg
        self.pub_frame.publish(msg)

    def publish_wrench(self):
        msg = WrenchStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        self.pub_wrench.publish(msg)

def main():
    rclpy.init()
    node = ComplianceDemo()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
