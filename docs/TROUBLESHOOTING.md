# Known Issue: RS485 Tool Communication Forwarder does not pass real Modbus traffic

## Symptom
Using Universal Robots' official RS485 URCap (Tool I/O → Controlled by: User)
+ ur_robot_driver's `use_tool_communication:=true` flag creates a working
TCP-to-pty bridge (`/tmp/ttyUR`) that accepts connections and bytes can be
sent successfully (confirmed via tcpdump — TCP handshake and data delivery
to the robot both work correctly). However, NO actual Modbus RTU response
is ever received back, regardless of:
- Correct baud rate / parity settings (115200, Even, matching gripper spec)
- Fresh restarts of the RS485 daemon
- Full physical power cycles of the robot arm
- Exact byte-for-byte requests matching manufacturer documentation
  (verified with both OnRobot RG6 and SCHUNK EGK 50 grippers — same result)

## What DOES work
Both grippers respond correctly and communicate reliably when controlled
through PolyScope's own native URCap (OnRobot Setup / SCHUNK EGU-EGK-EZU
Setup), which uses the UR controller's INTERNAL UART directly — this proves
the physical wiring, gripper, and protocol implementation are all correct.

## Conclusion
The issue is isolated to Universal Robots' RS485 Tool Communication Forwarder
URCap's TCP bridge itself — it does not appear to pass the internal UART
traffic through to the TCP socket transparently, despite accepting and
acknowledging the TCP connection and incoming bytes at the network level
(confirmed with tcpdump packet capture).

## Current workaround
Control grippers via PolyScope's native URCap (running a UR program with
gripper commands, e.g. RG Grip / SCHUNK grip nodes), while the arm itself
remains fully controlled via ROS2's ur_robot_driver. This hybrid approach
works reliably (see pick-and-place demo).

## Possible future investigation
- Check for UR firmware/URCap version-specific bugs or GitHub issues on
  Universal_Robots_ToolComm_Forwarder_URCap repo
- Try an alternative/older PolyScope or URCap version
- Contact Universal Robots support with the tcpdump evidence
