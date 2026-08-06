# SCHUNK EGK 50-MB-M-B Gripper — Setup Notes

## Identification
- Model: EGK 50-MB-M-B
- ID: 1491774
- Serial: BBPW4780
- Firmware: 5.2.0.81896
- Communication protocol: Modbus RTU
- Max stroke: 103.0 mm (hardware limit — see custom fingertip limit below)
- Max force: 300 N
- Max speed: 130 mm/s

## Documentation
Official docs downloaded from schunk.com (search by ID 1491774):
- EGK Operating manual.pdf
- EGU-EGK-EZU Commissioning instructions for Universal Robots (e-Series).pdf
- EGK V5.3.X Commissioning instructions for Modbus RTU.pdf
- URCap file used: egk-1.0.6.urcap

## Mechanical mounting
- Requires an ISO 50 adapter plate (not included with the gripper) to mount
  on the UR5e wrist — we 3D printed ours (design by Marouane).
- Custom yellow fingertips 3D printed specifically for the doll head shape.

## CRITICAL: Functional ground (mise à la terre) is required
Since our adapter plate is plastic (3D printed), there is NO electrical
continuity between the gripper housing and the robot chassis.
A separate ground wire MUST be connected:
- Locate the ground-marked (⏚) screw hole on the gripper's metal housing
  (NOT on the adapter, NOT the signal GND inside the cable)
- Connect a wire (NOT green-yellow colored) with cable lugs on both ends,
  from this point to a known ground point on the robot
- Stack order on the screw: toothed lock washer → cable lug → washer → screw
- Torque: 2 Nm
Without this, the gripper will not power on properly (no LEDs at all).

## Wiring — UR e-Series direct connection
| Signal | Gripper pin | Robot pin |
|--------|-------------|-----------|
| V+     | 1           | 5, 7      |
| BUS_A  | 2           | 1         |
| GND    | 3           | 6, 8      |
| BUS_B  | 4           | 2         |
| n.c.   | 5           | 3, 4      |

Connects directly to the UR5e's tool flange connector (same physical port
used by the OnRobot RG6) — no external power supply or gateway box needed.

## Tool I/O settings (PolyScope)
Installation → General → Tool I/O:
- Controlled by: EGU/EGK/EZU
- Baud Rate: 115200
- Parity: Even
- Stop Bits: One
(These match SCHUNK's documented Modbus RTU
## Verified working (July 23)
- New fingertip (reprinted after collision) mounted, tested successfully
- Release, Outside Grip, Move to Position all confirmed working via
  PolyScope Testing tab
- Max Position 75.0mm confirmed safe with new fingertip (no collision)
- Grip force test confirmed reasonable
