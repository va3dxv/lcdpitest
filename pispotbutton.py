#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import datetime
import pytz
import requests
import xmltodict

LCD_RS = 26
LCD_E = 19
LCD_D4 = 13
LCD_D5 = 6
LCD_D6 = 5
LCD_D7 = 11

LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0  # LCD RAM address for lines

E_PULSE = 0.0005
E_DELAY = 0.0005

def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT)  # RS
    GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
    GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
    GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
    GPIO.setup(LCD_D7, GPIO.OUT)  # DB7
    GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    lcd_init()

    input_vhf = GPIO.input(9)
    input_ten = GPIO.input(10)

    if input_vhf == False:

        while True:

            xml_vhf = requests.get(
                url="http://dxlite.g7vjr.org/?xml=1&band=vhf&dxcc=001&limit=5")
            spots_vhf = xmltodict.parse(xml_vhf.text)

            lcd_string("Showing last 5", LCD_LINE_1)
            lcd_string("DX Spots: 50Mhz+", LCD_LINE_2)
            time.sleep(3)
            for spots in spots_vhf["spots"]["spot"]:
                date_string = spots["time"]
                utc = pytz.utc
                est = pytz.timezone("US/Eastern")
                utc_datetime = utc.localize(
                    datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S"))
                lcd_string(spots["spotter"] + "->" + spots["dx"], LCD_LINE_1)
                lcd_string(spots["frequency"].split(".")[0] + " " + utc_datetime.astimezone(
                    est).strftime("%d%b") + utc_datetime.astimezone(est).strftime("%H:%M"), LCD_LINE_2)
                time.sleep(3)
            return main()

    elif input_ten == False:

        while True:

            xml_ten = requests.get(
                url="http://dxlite.g7vjr.org/?xml=1&band=10&dxcc=001&limit=5")
            spots_ten = xmltodict.parse(xml_ten.text)

            lcd_string("Showing last 5", LCD_LINE_1)
            lcd_string("DX Spots: 10M", LCD_LINE_2)
            time.sleep(3)
            for spots in spots_ten["spots"]["spot"]:
                date_string = spots["time"]
                utc = pytz.utc
                est = pytz.timezone("US/Eastern")
                utc_datetime = utc.localize(
                    datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S"))
                lcd_string(spots["spotter"] + "->" + spots["dx"], LCD_LINE_1)
                lcd_string(spots["frequency"].split(".")[0] + " " + utc_datetime.astimezone(
                    est).strftime("%d%b") + utc_datetime.astimezone(est).strftime("%H:%M"), LCD_LINE_2)
                time.sleep(3)
            return main()

    else:
        return main()

def lcd_init():
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # mode = True  for character
    #        False for command

    GPIO.output(LCD_RS, mode)  # RS

    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)

    lcd_toggle_enable()

    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)

    lcd_toggle_enable()

def lcd_toggle_enable():
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_string(message, line):

    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)
        lcd_string("Goodbye!", LCD_LINE_1)
        time.sleep(3)
        lcd_byte(0x01, LCD_CMD)
        GPIO.cleanup()