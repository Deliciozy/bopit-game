# code.py
# Simple Bop-It style handheld game for XIAO ESP32C3 + SSD1306 + ADXL345 + Rotary Encoder + NeoPixel
# 尽量用最简单的状态机实现所有要求

import time
import board
import busio
import digitalio
import displayio
import terminalio
import neopixel

from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x
from adafruit_debouncer import Debouncer
from rotary_encoder import RotaryEncoder

# ---------- 全局常量 ----------

MAX_LEVEL = 10

# 玩家可执行的四种动作
MOVE_KNOB_LEFT = 0
MOVE_KNOB_RIGHT = 1
MOVE_SHAKE = 2
MOVE_BUTTON = 3

MOVE_NAMES = {
    MOVE_KNOB_LEFT: "TURN LEFT",
    MOVE_KNOB_RIGHT: "TURN RIGHT",
    MOVE_SHAKE: "SHAKE",
    MOVE_BUTTON: "PRESS BTN",
}

# 游戏状态
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_WIN = 3

# 难度设置：时间限制随等级变化
# base_time: 第一关时间，per_level: 每升一级减少的时间
DIFFICULTIES = [
    ("EASY",   5.0, 0.20),  # 原来 3.0，现在更宽松
    ("MEDIUM", 4.0, 0.25),  # 原来 2.5
    ("HARD",   3.0, 0.30),  # 原来 2.0
]

MIN_TIME_LIMIT = 1.5  # 原来 0.8，现在最低也有 1.5 秒

# EMA 滤波参数
ACC_ALPHA = 0.3    # 越小越平滑
SHAKE_THRESHOLD = 3.0  # m/s^2, 超过认为是“摇一摇”

# ---------- 显示初始化 ----------

displayio.release_displays()

i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# 简单助手：清屏并显示最多 3 行文字
def show_text(line1="", line2="", line3=""):
    main_group = displayio.Group()
    lines = [line1, line2, line3]
    # 垂直布局：三行大致均匀分布
    for i, text in enumerate(lines):
        if not text:
            continue
        lbl = label.Label(terminalio.FONT, text=text)
        w = lbl.bounding_box[2]
        h = lbl.bounding_box[3]
        lbl.x = (display.width - w) // 2
        # 64 高度，行 0,1,2 分别放在 16, 32, 48 附近
        lbl.y = 16 + i * 16 + h // 2
        main_group.append(lbl)
    display.root_group = main_group

# ---------- NeoPixel 初始化 ----------

PIXEL_PIN = board.D10
NUM_PIXELS = 1
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.3, auto_write=True)

def set_pixel(color):
    pixels[0] = color

COLOR_OFF    = (0, 0, 0)
COLOR_RED    = (50, 0, 0)
COLOR_GREEN  = (0, 50, 0)
COLOR_BLUE   = (0, 0, 50)
COLOR_YELLOW = (50, 50, 0)
COLOR_MAGENTA = (50, 0, 50)
COLOR_CYAN   = (0, 50, 50)
COLOR_WHITE  = (50, 50, 50)

# ---------- 旋转编码器 + 按钮 初始化 ----------

# 旋钮 A/B —— 调高灵敏度：pulses_per_detent = 1
encoder = RotaryEncoder(board.D3, board.D2, debounce_ms=3, pulses_per_detent=1)
encoder_last_pos = 0

# 主按钮：外接单独按钮，接在 D6（用于菜单选择 / PRESS BTN / RESTART）
btn_pin = digitalio.DigitalInOut(board.D6)
btn_pin.direction = digitalio.Direction.INPUT
btn_pin.pull = digitalio.Pull.UP
button = Debouncer(btn_pin)

# 旋钮自带按钮（D8）不再使用，可以不接或忽略

# ---------- 加速度计初始化 + 校准 + 滤波 ----------

accelerometer = adafruit_adxl34x.ADXL345(i2c)

# 零点偏移基线
baseline_x = 0.0
baseline_y = 0.0
baseline_z = 0.0

# EMA 滤波后的值
filtered_x = 0.0
filtered_y = 0.0
filtered_z = 0.0

def calibrate_accel():
    global baseline_x, baseline_y, baseline_z
    show_text("CALIBRATING", "KEEP STILL", "")
    set_pixel(COLOR_YELLOW)
    time.sleep(0.5)

    samples = 40
    sum_x = sum_y = sum_z = 0.0
    for _ in range(samples):
        x, y, z = accelerometer.acceleration
        sum_x += x
        sum_y += y
        sum_z += z
        time.sleep(0.02)

    baseline_x = sum_x / samples
    baseline_y = sum_y / samples
    baseline_z = sum_z / samples

    show_text("CALIB DONE", "", "")
    time.sleep(0.5)

def read_filtered_accel():
    """读取加速度计，加上零点校正 + EMA 滤波"""
    global filtered_x, filtered_y, filtered_z
    raw_x, raw_y, raw_z = accelerometer.acceleration
    # 零点校正
    raw_x -= baseline_x
    raw_y -= baseline_y
    raw_z -= baseline_z

    # EMA 滤波
    filtered_x = ACC_ALPHA * raw_x + (1 - ACC_ALPHA) * filtered_x
    filtered_y = ACC_ALPHA * raw_y + (1 - ACC_ALPHA) * filtered_y
    filtered_z = ACC_ALPHA * raw_z + (1 - ACC_ALPHA) * filtered_z

    return filtered_x, filtered_y, filtered_z

def detect_shake():
    """通过幅度判断是否摇动"""
    fx, fy, fz = read_filtered_accel()
    magnitude = (fx * fx + fy * fy + fz * fz) ** 0.5
    return magnitude > SHAKE_THRESHOLD

# ---------- 工具函数 ----------

def get_time_limit_for_level(level, base_time, per_level):
    t = base_time - (level - 1) * per_level
    if t < MIN_TIME_LIMIT:
        t = MIN_TIME_LIMIT
    return t

def get_encoder_delta():
    """返回旋钮方向：负值左，正值右"""
    global encoder_last_pos
    changed = encoder.update()
    if not changed:
        return 0
    pos = encoder.position
    delta = pos - encoder_last_pos
    encoder_last_pos = pos
    return delta

# ---------- 游戏逻辑 ----------

def menu_select_difficulty():
    """使用旋钮在三档难度中选择，按按钮确认"""
    idx = 0
    set_pixel(COLOR_BLUE)
    while True:
        button.update()
        delta = get_encoder_delta()
        if delta != 0:
            step = 1 if delta > 0 else -1
            idx += step
            if idx < 0:
                idx = 0
            if idx >= len(DIFFICULTIES):
                idx = len(DIFFICULTIES) - 1

        name, base_t, per_level = DIFFICULTIES[idx]
        show_text("SELECT DIFFICULTY", f"> {name} <", "PRESS BTN TO START")

        if button.fell:
            set_pixel(COLOR_GREEN)
            time.sleep(0.2)
            return DIFFICULTIES[idx]

        time.sleep(0.05)

def choose_random_move(level):
    # 简化：一直允许四种动作随机
    import random
    return random.choice([MOVE_KNOB_LEFT, MOVE_KNOB_RIGHT, MOVE_SHAKE, MOVE_BUTTON])

def play_game(base_time, per_level):
    """主游戏循环：返回 True=win, False=game over"""
    state = STATE_PLAYING
    level = 1

    # 重置 NeoPixel
    set_pixel(COLOR_BLUE)

    while state == STATE_PLAYING:
        # 为当前关卡选择一个动作
        target_move = choose_random_move(level)
        level_time_limit = get_time_limit_for_level(level, base_time, per_level)

        start_time = time.monotonic()
        success = False
        wrong = False

        # 清一次加速度读取，避免旧值
        read_filtered_accel()

        while True:
            now = time.monotonic()
            elapsed = now - start_time
            remaining = level_time_limit - elapsed
            if remaining < 0:
                remaining = 0

            # 更新输入
            button.update()
            delta = get_encoder_delta()
            shake = detect_shake()

            # 显示当前信息（等级 + 动作 + 剩余时间）
            show_text(
                f"LEVEL {level}",
                MOVE_NAMES[target_move],
                f"TIME: {remaining:0.1f}s"
            )

            # 默认等待状态灯：蓝色
            set_pixel(COLOR_BLUE)

            # 判断玩家动作 —— 先看旋钮方向，再看按钮，最后看摇一摇
            performed_move = None

            if delta < 0:
                performed_move = MOVE_KNOB_LEFT
            elif delta > 0:
                performed_move = MOVE_KNOB_RIGHT
            elif button.fell:
                performed_move = MOVE_BUTTON
            elif shake:
                performed_move = MOVE_SHAKE

            if performed_move is not None:
                if performed_move == target_move:
                    success = True
                    break
                else:
                    wrong = True
                    break

            if elapsed > level_time_limit:
                # 超时
                wrong = True
                break

            time.sleep(0.02)

        if success:
            # 成功提示
            set_pixel(COLOR_GREEN)
            show_text(f"LEVEL {level}", "GOOD!", "")
            time.sleep(0.5)
            level += 1
            if level > MAX_LEVEL:
                state = STATE_WIN
        else:
            state = STATE_GAME_OVER

    return state == STATE_WIN

def game_over_screen():
    set_pixel(COLOR_RED)
    show_text("GAME OVER", "PRESS BTN", "TO RESTART")
    # 等待按钮
    while True:
        button.update()
        _ = get_encoder_delta()  # 清旋钮
        if button.fell:
            time.sleep(0.2)
            break
        time.sleep(0.05)

def win_screen():
    # 简单彩色循环几秒
    colors = [COLOR_GREEN, COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW, COLOR_WHITE]
    start = time.monotonic()
    while time.monotonic() - start < 3.0:
        for c in colors:
            set_pixel(c)
            show_text("YOU WIN!", "CONGRATS", "")
            time.sleep(0.2)
    # 停在绿色
    set_pixel(COLOR_GREEN)
    show_text("YOU WIN!", "PRESS BTN", "TO RESTART")
    while True:
        button.update()
        _ = get_encoder_delta()
        if button.fell:
            time.sleep(0.2)
            break
        time.sleep(0.05)

# ---------- 主程序入口 ----------

calibrate_accel()

while True:
    # 1. 难度选择界面
    name, base_time, per_level = menu_select_difficulty()

    # 2. 显示即将开始
    show_text("READY?", name, "GET SET...")
    set_pixel(COLOR_BLUE)
    time.sleep(1.0)

    # 3. 游戏过程
    win = play_game(base_time, per_level)

    # 4. 结束/胜利界面（不用重启可再玩）
    if win:
        win_screen()
    else:
        game_over_screen()

