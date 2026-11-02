
import math
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from my_robot_interfaces.action import Rotate


class RotateServer(Node):

    def __init__(self):
        super().__init__('rotate_server')

        self.declare_parameter('turn_speed', 0.5)

        self.callback_group = ReentrantCallbackGroup()

        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10,
            callback_group=self.callback_group
        )

        self.lock = threading.Lock()

        self.previous_yaw = None
        self.total_yaw = 0.0
        self.odom_received = False

        self.action_server = ActionServer(
            self,
            Rotate,
            '/rotate',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info('Rotate action server started')

    def get_yaw(self, msg):

        q = msg.pose.pose.orientation

        sin_yaw = 2.0 * (q.w * q.z + q.x * q.y)
        cos_yaw = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)

        return math.atan2(sin_yaw, cos_yaw)

    def odom_callback(self, msg):

        current_yaw = self.get_yaw(msg)

        with self.lock:

            if self.previous_yaw is None:
                self.previous_yaw = current_yaw
                self.odom_received = True
                return

            delta = current_yaw - self.previous_yaw

            # Handle yaw wrapping at -pi and pi
            delta = math.atan2(
                math.sin(delta),
                math.cos(delta)
            )

            self.total_yaw += delta
            self.previous_yaw = current_yaw

    def goal_callback(self, goal_request):

        if goal_request.angle == 0.0:
            self.get_logger().warning('Zero rotation angle rejected')
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):

        self.get_logger().info('Rotation cancellation requested')
        return CancelResponse.ACCEPT

    def publish_stop(self):

        self.publisher.publish(Twist())

    def execute_callback(self, goal_handle):

        self.get_logger().info('Starting rotation')

        # Wait until odometry is available
        while rclpy.ok() and not self.odom_received:

            if goal_handle.is_cancel_requested:
                self.publish_stop()
                goal_handle.canceled()
                return Rotate.Result()

            time.sleep(0.05)

        with self.lock:
            start_yaw = self.total_yaw

        target_angle = goal_handle.request.angle

        direction = 1.0 if target_angle > 0 else -1.0

        turn_speed = self.get_parameter(
            'turn_speed'
        ).value

        velocity = Twist()
        velocity.angular.z = direction * turn_speed

        feedback_msg = Rotate.Feedback()
        result = Rotate.Result()

        rate = self.create_rate(20)

        try:
            while rclpy.ok():

                if goal_handle.is_cancel_requested:
                    self.publish_stop()
                    goal_handle.canceled()

                    with self.lock:
                        result.turned = self.total_yaw - start_yaw

                    return result

                with self.lock:
                    turned = self.total_yaw - start_yaw

                progress = turned * direction

                feedback_msg.turned = float(turned)
                goal_handle.publish_feedback(feedback_msg)

                if progress >= abs(target_angle):
                    break

                self.publisher.publish(velocity)

                rate.sleep()

        except Exception as error:
            self.get_logger().error(f'Rotation error: {error}')
            self.publish_stop()
            goal_handle.abort()

            with self.lock:
                result.turned = self.total_yaw - start_yaw

            return result

        self.publish_stop()

        with self.lock:
            result.turned = self.total_yaw - start_yaw

        goal_handle.succeed()

        self.get_logger().info(
            f'Rotation completed: {result.turned:.3f} radians'
        )

        return result


def main(args=None):

    rclpy.init(args=args)

    node = RotateServer()

    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)

    try:
        executor.spin()

    except KeyboardInterrupt:
        pass

    finally:
        node.publish_stop()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

