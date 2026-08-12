# ROBOTA-SUDOE — UR5e ROS2 Control Stack

**Lab:** CiTIUS, Universidade de Santiago de Compostela, Spain  
**Project:** ROBOTA-SUDOE (Interreg Sudoe)  
**Robot:** Universal Robots UR5e on Robotnik KAIROS mobile base  
**OS:** Ubuntu 24.04 | **ROS2:** Jazzy Jalisco  

---

## What is this project?

This repository contains the complete ROS2 software stack to control a **UR5e robotic arm** for a collaborative human-robot interaction task (demolding and assembly of doll parts). A human operator guides the robot by applying forces through a handle equipped with a force/torque sensor. The robot responds compliantly — this is called **admittance control**.

If you are new to this lab and this robot, read this entire README before touching anything.

---

## Hardware Overview

| Component | Description | IP / Port |
|-----------|-------------|-----------|
| UR5e arm | 6-DOF collaborative robot | `192.168.0.210` |
| Robotnik KAIROS | Mobile base carrying the UR5e | — |
| Onboard PC | Ubuntu 24.04 PC inside the KAIROS base | `192.168.0.183` |
| SCHUNK EGK 50 | 2-finger electric gripper on the arm flange | TCP port `55050` |
| Bota HEX-E v2 | 6-axis force/torque sensor (EtherCAT) | `enp3s0` NIC |
| VNC | Remote desktop access to PolyScope (teach pendant) | password: `easybot` |

**Safety password for PolyScope:** `ur`

---

## Repository Structure

```
robota-sudoe-ur5e-ros2/
├── README.md                          ← you are here
├── config/
│   └── bota_hex_e.json               ← Bota sensor configuration file
├── admittance_control_ros2.cpp        ← C++ admittance control node (source)
├── admittance_control_ros2_CMakeLists.txt
├── admittance_control_ros2_package.xml
├── force_sensor_eth_publisher_ros2.py ← Bota sensor offset correction node
├── ur_force_zeroed.py                 ← UR internal sensor offset correction node
├── schunk_gripper_node.py             ← SCHUNK gripper ROS2 node
├── compliance_demo.py                 ← Cartesian compliance controller demo
├── fastdds_no_shm.xml                 ← FastDDS config (fixes root/user DDS isolation)
└── docs/                             ← Additional documentation
```

---

## Software Stack (installed on onboard PC)

All of this is already installed on the onboard PC (`kairos@robot`). You do NOT need to reinstall anything.

```
~/kairos_ws/src/
├── cartesian_controllers_universal_robots/   ← Cartesian compliance/force/motion controllers
├── bota_ft_sensor_driver/                    ← Bota EtherCAT sensor driver (modified for gen0)
├── admittance_control_ros2/                  ← Admittance control ROS2 package
└── bota_standalone/                          ← Standalone Bota reader (alternative)
```

---

## Step-by-Step Startup (do this every time)

### Step 1 — Power on hardware

1. Turn on the **UR5e controller box** (physical power button on the box)
2. Wait for PolyScope to boot on the teach pendant (~1 minute)
3. Power on the **Bota sensor junction box**
4. Make sure the **Ethernet cable** from the Bota box is plugged into the Robotnik LAN port

### Step 2 — Connect to the onboard PC

The onboard PC is inside the Robotnik base. Connect a keyboard/monitor directly, or SSH from your laptop if you are on the same network:

```bash
ssh kairos@192.168.0.183
# password: kairos (ask the lab)
```

### Step 3 — Configure the network interfaces

Run this every time after a reboot (the IP is not persistent):

```bash
sudo ip addr add 192.168.1.101/24 dev enp3s0
sudo ethtool -C enp3s0 rx-usecs 0 tx-usecs 0
sudo ethtool -K enp3s0 gso off gro off tso off
```

### Step 4 — Open PolyScope via VNC (remote desktop)

```bash
xtigervncviewer 192.168.0.210 &
```
Password: `easybot`

In PolyScope:
- Click **START** on the startup screen
- Wait for all **5 green checkmarks** to appear
- Click the mode button (top right) → select **Remote Control**

### Step 5 — Launch the arm ROS2 controllers

Open a terminal (leave it running — do NOT close it):

```bash
source /opt/ros/jazzy/setup.bash
source ~/kairos_ws/install/setup.bash
ros2 launch cartesian_controllers_universal_robots robot_ur5e.launch.py robot_ip:=192.168.0.210
```

Wait until you see:
```
[ros2_control_node]: Robot connected to reverse interface. Ready to receive control commands.
```

### Step 6 — Load and play the robot program

In a new terminal:

```bash
python3 ~/send_dashboard.py "load ext_control.urp" "play"
```

This loads the External Control program and starts it. The arm is now under ROS2 control.

### Step 7 — Start the Bota force/torque sensor

In a new terminal (leave it running):

```bash
sudo bash -c "FASTRTPS_DEFAULT_PROFILES_FILE=/home/kairos/fastdds_no_shm.xml \
  source /opt/ros/jazzy/setup.bash && \
  source /home/kairos/kairos_ws/install/setup.bash && \
  ros2 launch rokubimini_ethercat rokubimini_ethercat.launch.py"
```

Wait until you see: `Starting Worker at 10 Hz`

### Step 8 — Start the force sensor publisher

In a new terminal (leave it running):

```bash
python3 ~/force_sensor_eth_publisher_ros2.py
```

Wait until you see: `Offset computed` — the sensor is now zeroed and publishing.

### Step 9 — Start the SCHUNK gripper node

In a new terminal (leave it running):

```bash
python3 ~/schunk_gripper_node.py
```

---

## Verify Everything is Working

Check all ROS2 topics are active:

```bash
source ~/kairos_ws/install/setup.bash

# Arm joint states (should show 6 joints at ~500Hz)
ros2 topic hz /joint_states

# Bota sensor (should show ~10Hz)
ros2 topic hz /force_sensor_eth

# Bota raw values (should be near zero at rest)
ros2 topic echo /force_sensor_eth --once

# UR internal F/T sensor
ros2 topic echo /ft_sensor_wrench --once

# Gripper position (mm)
ros2 topic echo /gripper/position --once
```

---

## Running the Admittance Control

Admittance control makes the robot move in response to forces you apply to the handle — like a collaborative, force-guided robot.

### Option A — With Bota sensor (RECOMMENDED — requires correct mechanical assembly)

The Bota sensor must be mounted **between the arm flange and the handle** (not below the handle). Correct order from top to bottom: **flange → Bota sensor → handle → gripper**.

```bash
# Switch to velocity controller
ros2 service call /controller_manager/switch_controller \
  controller_manager_msgs/srv/SwitchController \
  "{activate_controllers: ['forward_velocity_controller'], \
    deactivate_controllers: ['scaled_joint_trajectory_controller'], \
    strictness: 2}"

# Run admittance node
~/kairos_ws/install/admittance_control_ros2/lib/admittance_control_ros2/admittance_control_node \
  --ros-args -p sensor:=ethercat
```

### Option B — With UR internal sensor (no Bota needed, but needs gravity compensation)

```bash
# Zero the UR sensor first (keep robot still for 5 seconds)
python3 ~/ur_force_zeroed.py &
sleep 6

# Switch to velocity controller
ros2 service call /controller_manager/switch_controller \
  controller_manager_msgs/srv/SwitchController \
  "{activate_controllers: ['forward_velocity_controller'], \
    deactivate_controllers: ['scaled_joint_trajectory_controller'], \
    strictness: 2}"

# Run admittance node (rotation disabled, translation only)
~/kairos_ws/install/admittance_control_ros2/lib/admittance_control_ros2/admittance_control_node \
  --ros-args \
  -p sensor:=UR \
  -p M_trans:=30.0 \
  -p dead_cart:=5.0 \
  -p dead_rot:=100.0 \
  -p freq:=50.0 \
  -r /ft_sensor_wrench:=/force_sensor_ur_zeroed
```

### Admittance Parameters Explained

| Parameter | Meaning | Effect of increasing |
|-----------|---------|---------------------|
| `M_trans` | Virtual mass (kg) | Heavier, slower to start |
| `M_rot` | Virtual rotational inertia | Heavier rotation |
| `c` | Damping ratio | More friction, stops faster |
| `F_alpha` | Force filter (0–1) | Smoother but slower response |
| `V_alpha` | Velocity filter (0–1) | Smoother joint commands |
| `dead_cart` | Force dead zone (N) | Ignores smaller forces |
| `dead_rot` | Torque dead zone (Nm) | Ignores smaller torques |
| `freq` | Control frequency (Hz) | Faster but more CPU |

---

## SCHUNK Gripper Control

```bash
# Open gripper
ros2 topic pub --once /gripper/action std_msgs/msg/String "data: 'open'"

# Close gripper
ros2 topic pub --once /gripper/action std_msgs/msg/String "data: 'close'"

# Move to specific position (in mm, max 75mm)
ros2 topic pub --once /gripper/command std_msgs/msg/Float64 "data: 45.0"
```

---

## Pick and Place Demo

A complete pick-and-place script combining arm + gripper is available:

```bash
python3 ~/pick_and_place_unified.py
```

This moves the arm through a pre-programmed pick-and-place sequence while opening/closing the gripper.

---

## Common Problems and Fixes

### "No slaves have been found" (Bota sensor)
- Check that the Bota box is powered on
- Check the Ethernet cable is connected
- Run: `sudo ip addr add 192.168.1.101/24 dev enp3s0`
- Check: `sudo ethtool enp3s0 | grep "Link detected"` → must say `yes`

### "Package not found" when running ROS2 commands
```bash
source /opt/ros/jazzy/setup.bash
source ~/kairos_ws/install/setup.bash
```

### Protective stop (C153A0, C157A0) during admittance
- Press **Continue** in PolyScope
- Make sure the robot is in **Normal mode** (not Reduced mode)
- Move robot to home position using freedrive if in reduced mode
- Increase `dead_cart` parameter to reduce sensitivity

### Robot program stops unexpectedly
```bash
python3 ~/send_dashboard.py "play"
```

### FastDDS warning about shared memory
This is normal. The `fastdds_no_shm.xml` file fixes the root/user DDS isolation. It is loaded automatically via `~/.bashrc`.

---

## Key Topics Reference

| Topic | Type | Description |
|-------|------|-------------|
| `/joint_states` | `sensor_msgs/JointState` | Live joint positions |
| `/ft_sensor_wrench` | `geometry_msgs/WrenchStamped` | UR5e internal F/T sensor |
| `/force_sensor_eth` | `geometry_msgs/WrenchStamped` | Bota sensor (offset-corrected) |
| `/gripper/action` | `std_msgs/String` | Gripper commands |
| `/gripper/position` | `std_msgs/Float64` | Live gripper position (mm) |
| `/forward_velocity_controller/commands` | `std_msgs/Float64MultiArray` | Joint velocity commands |
| `/cartesian_compliance_controller/current_pose` | `geometry_msgs/PoseStamped` | Live TCP pose |

---

## Contact

- **Lab supervisor:** Juan Antonio Corrales Ramón — CiTIUS, USC
- **Co-supervisor:** Saltanat Seitzhan — PhD researcher, CiTIUS
- **Developer:** Mohamed Ali Jomaa Ghouil — SIGMA Clermont / ENISo (May–Sept 2026)
- **Mechanical design:** Marouane Belhaddade Zanati — SIGMA Clermont (May–Sept 2026)
