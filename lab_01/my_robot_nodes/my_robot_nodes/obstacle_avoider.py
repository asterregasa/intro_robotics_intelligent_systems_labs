
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed
from std_srvs.srv import SetBool


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')

        # Parameters
        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('max_turn_speed', 1.5)

        # Robot starts disabled
        self.enabled = False

        # Publishers
        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.status_publisher = self.create_publisher(
            RobotStatus,
            '/robot_status',
            10
        )

        # Obstacle subscription
        self.subscription = self.create_subscription(
            ObstacleInfo,
            '/obstacle',
            self.obstacle_callback,
            10
        )

        # Enable/disable service
        self.enable_service = self.create_service(
            SetBool,
            '/turn_away_enable',
            self.enable_callback
        )

        # Change turning speed service
        self.turn_speed_service = self.create_service(
            SetTurnSpeed,
            '/set_turn_speed',
            self.set_turn_speed_callback
        )

        self.get_logger().info(
            'Obstacle avoider started (disabled)'
        )

    def enable_callback(self, request, response):

        self.enabled = request.data

        if not self.enabled:
            # Stop the robot when disabled
            self.publisher.publish(Twist())

            # Publish stopped status
            status = RobotStatus()
            status.state = 'stopped'
            status.obstacle_distance = 0.0
            self.status_publisher.publish(status)

        response.success = True

        if self.enabled:
            response.message = 'Obstacle avoidance enabled'
        else:
            response.message = 'Obstacle avoidance disabled'

        self.get_logger().info(response.message)

        return response

    def set_turn_speed_callback(self, request, response):

        new_speed = request.turn_speed
        max_speed = self.get_parameter('max_turn_speed').value

        if new_speed <= 0.0:
            response.success = False
            response.message = 'Turn speed must be greater than zero'

        elif new_speed > max_speed:
            response.success = False
            response.message = (
                f'Turn speed cannot exceed {max_speed}'
            )

        else:
            self.set_parameters([
                Parameter(
                    'turn_speed',
                    value=new_speed
                )
            ])

            response.success = True
            response.message = (
                f'Turn speed updated to {new_speed}'
            )

        self.get_logger().info(response.message)

        return response

    def obstacle_callback(self, msg):

        # Ignore obstacles while disabled
        if not self.enabled:
            return

        # Read current parameter values
        forward_speed = self.get_parameter(
            'forward_speed'
        ).value

        turn_speed = self.get_parameter(
            'turn_speed'
        ).value

        velocity = Twist()
        status = RobotStatus()

        if not msg.too_close:
            # Move forward
            velocity.linear.x = forward_speed
            velocity.angular.z = 0.0
            status.state = 'forward'

        else:
            # Turn away from the obstacle
            velocity.linear.x = 0.0

            if msg.angle > 0:
                # Obstacle on the left: turn right
                velocity.angular.z = -turn_speed
            else:
                # Obstacle on the right or directly ahead: turn left
                velocity.angular.z = turn_speed

            status.state = 'turning'

        status.obstacle_distance = msg.distance

        # Publish velocity and status
        self.publisher.publish(velocity)
        self.status_publisher.publish(status)


def main(args=None):

    rclpy.init(args=args)

    node = TurnAway()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


