# Session Startup Checklist — UR5e + RG6 + ROS2

## Network setup
- Laptop built-in Ethernet (`enp3s0`) → Robotnik panel "LAN" port → should get `192.168.0.100/24`
- USB-to-Ethernet adapter (`enx...`) → Bota EtherCAT box "IN" port → should get `192.168.1.101/24`
- ⚠️ If WiFi is also on `192.168.0.x`, routing breaks. Fix:
- Verify: `ping -c 4 192.168.0.210` should succeed (UR control box)

## 1. Power on hardware
- Robotnik base: power switch ON
- UR arm: "ON ARM" button on Robotnik panel
- Wait ~60-90 seconds after power-up before expecting network response

## 2. Connect to PolyScope
- Remmina → VNC → `192.168.0.210`, password `easybot`
- Click **START**, wait for 5 green checkmarks

## 3. CRITICAL: stop the onboard PC's conflicting ROS1 arm driver
The Robotnik onboard PC (sxlsk-210728aa) auto-launches its own ROS1
connection to the arm at boot. This MUST be stopped before ROS2 can
connect, or you'll get:
`FATAL: Variable 'speed_slider_mask' is currently controlled by another RTDE client`

```bash
ssh robot@192.168.0.200
screen -S arm_bringup -X quit
exit
```

## 4. Check/fix Tool I/O settings (for gripper serial comms)
PolyScope → Installation → General → Tool I/O
- If using OnRobot URCap: Controlled by = OnRobot (auto-configures baud/parity)
- If using RS485 direct: Controlled by = User, Baud Rate = 1M, Parity = Even
  (⚠️ these reset to defaults 2M/None after every robot reboot — always recheck)

## 5. Launch ROS2 arm driver (Terminal 1)
```bash
source /opt/ros/humble/setup.bash
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e \
  robot_ip:=192.168.0.210 launch_rviz:=true \
  use_tool_communication:=true tool_device_name:=/tmp/ttyUR
```
Wait for: `Successful 'activate' of hardware 'ur5e'`

## 6. Start External Control program on pendant
PolyScope → Program → open `ros2_control` → Play → Play from beginning
Confirm in Terminal 1: `Robot connected to reverse interface.`

## 7. (If using gripper via ROS2) Launch gripper driver (Terminal 2)
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch onrobot_driver onrobot_control.launch.py \
  onrobot_type:=rg6 connection_type:=serial
```
⚠️ Known issue: intermittent Modbus "slave 255 timeout" errors even with
correct config — root cause not yet fully resolved (see TROUBLESHOOTING.md).
Fallback: control gripper via PolyScope RG Grip nodes in a UR program instead.

## 8. Verify everything works
```bash
ros2 control list_controllers   # scaled_joint_trajectory_controller should be 'active'
ros2 topic echo /joint_states --once
```
