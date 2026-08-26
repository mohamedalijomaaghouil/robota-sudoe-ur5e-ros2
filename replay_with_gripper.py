#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64
from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import JointState
import sys
import time
import numpy as np

class BagReplayWithGripper(Node):
    def __init__(self):
        super().__init__('bag_replay_with_gripper')
        self.traj_pub = self.create_publisher(JointTrajectory, '/scaled_joint_trajectory_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(Float64, '/gripper/command', 10)

        # Gestion des arguments
        self.speed = 1.0
        if len(sys.argv) > 1 and sys.argv[1] == '--speed' and len(sys.argv) > 2:
            self.speed = float(sys.argv[2])
            self.bag_path = sys.argv[3] if len(sys.argv) > 3 else 'demolding_final_3/demolding_final_3_0.mcap'
        elif len(sys.argv) > 1:
            self.bag_path = sys.argv[1]
        else:
            self.bag_path = 'demolding_final_3/demolding_final_3_0.mcap'

        self.joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        self.get_logger().info(f'Loading bag: {self.bag_path}, speed: {self.speed}x')
        self.load_and_publish()

    def load_and_publish(self):
        storage_options = StorageOptions(uri=self.bag_path, storage_id='mcap')
        converter_options = ConverterOptions(input_serialization_format='cdr', output_serialization_format='cdr')
        reader = SequentialReader()
        reader.open(storage_options, converter_options)

        joint_positions = []
        timestamps = []
        gripper_commands = []
        start_time = None

        while reader.has_next():
            (topic, data, t) = reader.read_next()
            if topic == '/joint_states':
                msg = deserialize_message(data, JointState)
                if start_time is None:
                    start_time = t
                pos = []
                for name in self.joint_names:
                    if name in msg.name:
                        idx = msg.name.index(name)
                        pos.append(msg.position[idx])
                    else:
                        pos.append(0.0)
                joint_positions.append(pos)
                timestamps.append((t - start_time) / 1e9)
            elif topic == '/gripper/command':
                msg = deserialize_message(data, Float64)
                if start_time is None:
                    start_time = t
                gripper_commands.append(((t - start_time) / 1e9, msg.data))

        if not joint_positions:
            self.get_logger().error('No joint states found!')
            return

        # Ajuster le nombre de points pour la fluidité (step = //10 donne ~50 points)
        step = max(1, len(joint_positions) // 10)
        #step = 10 
        traj = JointTrajectory()
        traj.joint_names = self.joint_names
        points = []
        for i in range(0, len(joint_positions), step):
            pt = JointTrajectoryPoint()
            pt.positions = joint_positions[i]
            pt.velocities = [0.0] * 6
            pt.accelerations = [0.0] * 6
            t_scaled = timestamps[i] / self.speed
            pt.time_from_start.sec = int(t_scaled)
            pt.time_from_start.nanosec = int((t_scaled - int(t_scaled)) * 1e9)
            points.append(pt)
        traj.points = points
        self.get_logger().info(f'Publishing trajectory with {len(points)} points (speed {self.speed}x)')
        self.traj_pub.publish(traj)

        # Publier les commandes de la pince avec le timing ajusté
        if gripper_commands:
            self.get_logger().info(f'Publishing {len(gripper_commands)} gripper commands')
            start_time_real = time.time()
            for t_rel, pos in gripper_commands:
                t_scaled = t_rel / self.speed
                while time.time() - start_time_real < t_scaled:
                    rclpy.spin_once(self, timeout_sec=0.01)
                msg = Float64()
                msg.data = pos
                self.gripper_pub.publish(msg)
                self.get_logger().info(f'Gripper at {pos:.1f} mm at t={t_scaled:.1f}s')
        else:
            self.get_logger().info('No gripper commands found in bag')

def main(args=None):
    rclpy.init(args=args)
    node = BagReplayWithGripper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
