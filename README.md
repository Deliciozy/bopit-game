🕹️ Bop-It Style Handheld Game (ESP32-C3 + CircuitPython)

A 90s-style handheld electronic reaction game inspired by Bop It / Brain Warp, built using an ESP32-C3 microcontroller, SSD1306 OLED display, ADXL345 accelerometer, rotary encoder, LiPo battery, NeoPixel LED, and custom enclosure.

This project was designed and implemented as part of an embedded systems course, demonstrating sensor integration, real-time game logic, input processing, and hardware design.

📦 How to Play

Power on the device using the back power switch.

Use the rotary encoder to scroll through three difficulty levels:

Easy (slow timer)

Medium

Hard (fast timer)

Press the external button to confirm difficulty and start.

Each level, the OLED shows a random command:

TURN LEFT → rotate encoder counterclockwise

TURN RIGHT → rotate encoder clockwise

SHAKE → shake the whole device

PRESS BTN → press the main external button

You must perform the move within the time limit, which shortens as levels increase.

If correct → next level

If wrong or timeout → Game Over

Press button to restart without power-cycling

Beat all 10 levels → YOU WIN!

NeoPixel LED acts as a state indicator throughout gameplay.

🧩 Components Used
Microcontroller

Seeed Studio XIAO ESP32-C3 (running CircuitPython)

Sensors / Inputs

Rotary Encoder (direction input)

External Button (game actions)

ADXL345 Accelerometer (shake detection)

Outputs

SSD1306 128×64 OLED Display (game UI)

WS2812 NeoPixel LED (status indicator)

Power

LiPo Battery

Physical On/Off Toggle Switch

Battery wired through switch into ESP32 BAT pin

Device powered without USB

Enclosure

Laser-cut wooden box with:

Hole for encoder shaft

Opening for main action button

Side cutout for USB-C access

Removable lid for electronics

🧠 System Block Diagram

🔌 Circuit Diagram

The full circuit schematic is included as a PDF exported from KiCad:

📄 bopit_circuit.pdf

This includes wiring for:

I²C bus (OLED + accelerometer)

Rotary encoder A/B channels

Input button with pull-up

NeoPixel data + power

Battery and power switch

ESP32-C3 pin assignments

📐 Enclosure

Example of the finished enclosure:

<img src="docs/Enclosure.png" width="350">

Designed to:

Protect electronics

Provide solid mounting for sensors and buttons

Allow easy access to battery and USB-C port

🗂️ Repository Structure
bopit-game/
│
├── code/                # main CircuitPython code
│   └── code.py
│
├── lib/                 # required CircuitPython libraries
│
├── docs/
│   ├── system_diagram.png
│   ├── bopit_circuit.pdf
│   ├── Enclosure.png
│   └── bopit_circuit/   # KiCad source files
│
└── README.md

🚀 How to Run the Game

Install CircuitPython on the XIAO ESP32-C3

Copy the following into the ESP32 CIRCUITPY drive:

/code/code.py

/lib folder with required libraries

Disconnect USB and power via LiPo battery

Flip the power switch — the game begins!

🧪 Features Checklist (Matches Course Requirements)

✔ 3 difficulty modes
✔ Minimum 4 player input actions
✔ Time-limited moves
✔ 10+ increasing levels
✔ OLED shows level & move
✔ Game Over + restart without power cycle
✔ Win screen
✔ Accelerometer calibrated + filtered
✔ NeoPixel integrated
✔ LiPo battery + safe power switch
✔ Complete schematic diagram
✔ System block diagram
✔ Enclosure demonstrating proper hardware housing
✔ Organized GitHub repo

✅ 9. Requirements Checklist
Requirement	Status
Three difficulty settings	✔ Implemented
Four unique player moves	✔ TURN LEFT / RIGHT, SHAKE, PRESS
Time-limited input	✔ Timer shown on OLED
Ten levels	✔ LEVEL 1–10
OLED shows Level + Move	✔ Yes
Game Over screen	✔ Yes
Restart without power cycle	✔ Yes
Win screen	✔ Rainbow animation
Sensor calibration/filtering	✔ ADXL345 EMA filter + calibration
NeoPixel used in gameplay	✔ Status indicator
Proper battery + switch wiring	✔ Implemented
Enclosure	✔ Screwed, printed enclosure
GitHub repo includes code, diagrams, README	✔ Yes