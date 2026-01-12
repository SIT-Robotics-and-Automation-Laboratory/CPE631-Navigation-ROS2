#!/usr/bin/env python3

from math import atan2, cos, pi, sin
import os
import time

import subprocess

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from ament_index_python.packages import get_package_share_directory


class PedestrianManager(Node):
    def __init__(self):
        super().__init__('pedestrian_manager')
        self.declare_parameter('world_name', 'cafe_world')
        self.declare_parameter('model_variant', 'person_standing')
        self.declare_parameter('target_model', 'Target')
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, False)])

        self.world_name = self.get_parameter('world_name').get_parameter_value().string_value
        self.model_variant = self.get_parameter('model_variant').get_parameter_value().string_value
        self.target_model = self.get_parameter('target_model').get_parameter_value().string_value

        self.package_share = get_package_share_directory('cpe631_ros2')
        self.models_path = os.path.join(self.package_share, 'models')

        self.gz_set_pose_service = f'/world/{self.world_name}/set_pose'
        self._last_set_pose_error = 0.0

        time.sleep(2.0)
        self._spawn_target(3.0, 9.5)

        self.pedestrians = {
            'ped_1': {'start': (3.0, 5.0), 'end': (3.0, -8.0), 'speed': 1.2, 'current': (3.0, 5.0), 'direction': 1},
            'ped_2': {'start': (-3.0, 5.0), 'end': (-3.0, 0.0), 'speed': 0.8, 'current': (-3.0, 5.0), 'direction': 1},
            'ped_3': {'start': (2.0, -4.5), 'end': (-3.0, -4.0), 'speed': 0.8, 'current': (2.0, -4.5), 'direction': 1},
            'ped_4': {'start': (0.0, 6.0), 'end': (3.5, 6.5), 'speed': 0.5, 'current': (0.0, 6.0), 'direction': 1},
        }

        for name, data in self.pedestrians.items():
            px, py = data['current']
            yaw = self._get_yaw(data['start'], data['end'])
            self._spawn_pedestrian(name, px, py, yaw)

        self.timer = self.create_timer(0.1, self._update_positions)

    def _spawn_target(self, px, py):
        target_path = os.path.join(self.models_path, self.target_model, 'model.sdf')
        self._spawn_entity('target', target_path, px, py, 0.19, 0.0)

    def _spawn_pedestrian(self, model_name, px, py, yaw):
        model_path = os.path.join(self.models_path, self.model_variant, 'model.sdf')
        self._spawn_entity(model_name, model_path, px, py, 0.0, yaw)

    def _spawn_entity(self, name, sdf_path, px, py, pz, yaw):
        if not os.path.exists(sdf_path):
            self.get_logger().error(f'Model file not found: {sdf_path}')
            return
        env = os.environ.copy()
        env['GZ_SIM_RESOURCE_PATH'] = f"{self.models_path}:{env.get('GZ_SIM_RESOURCE_PATH', '')}"
        command = [
            'ros2', 'run', 'ros_gz_sim', 'create',
            '-world', self.world_name,
            '-name', name,
            '-file', sdf_path,
            '-x', str(px),
            '-y', str(py),
            '-z', str(pz),
            '-Y', str(yaw),
        ]
        self.get_logger().info(f'cmd: {" ".join(command)}')
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            self.get_logger().error(
                f'Failed to spawn entity {name}: {result.stderr.strip()}'
            )

    def _update_positions(self):
        for name, data in self.pedestrians.items():
            current_x, current_y = data['current']
            target_x, target_y = data['end'] if data['direction'] == 1 else data['start']
            dx = target_x - current_x
            dy = target_y - current_y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            step_size = data['speed'] / 10.0
            if distance <= step_size:
                data['direction'] *= -1
                new_x, new_y = target_x, target_y
            else:
                ratio = step_size / distance
                new_x = current_x + ratio * dx
                new_y = current_y + ratio * dy
            yaw = self._get_yaw((current_x, current_y), (new_x, new_y))
            self._set_pose(name, new_x, new_y, 0.0, yaw)
            data['current'] = (new_x, new_y)

    def _set_pose(self, name, px, py, pz, yaw):
        request = self._gz_pose_request(name, px, py, pz, yaw)
        command = [
            'gz', 'service',
            '-s', self.gz_set_pose_service,
            '--reqtype', 'gz.msgs.Pose',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '2000',
            '--req', request,
        ]
        env = os.environ.copy()
        env.setdefault('GZ_IP', '127.0.0.1')
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            now = time.time()
            if now - self._last_set_pose_error > 5.0:
                detail = result.stderr.strip() or result.stdout.strip()
                self.get_logger().warning(f'Failed to move {name}: {detail}')
                self._last_set_pose_error = now

    def _gz_pose_request(self, name, px, py, pz, yaw):
        qz = sin(yaw / 2.0)
        qw = cos(yaw / 2.0)
        return (
            f'name: "{name}" '
            f'position {{ x: {px:.6f} y: {py:.6f} z: {pz:.6f} }} '
            f'orientation {{ x: 0 y: 0 z: {qz:.6f} w: {qw:.6f} }}'
        )

    def _get_yaw(self, start, end):
        return atan2(end[1] - start[1], end[0] - start[0]) + pi / 2


def main():
    rclpy.init()
    node = PedestrianManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
