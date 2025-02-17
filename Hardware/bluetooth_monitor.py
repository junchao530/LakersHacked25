import serial
import pandas

comPort = input("Enter com port (ALL CAPS!): ")
print("Attempting connection to: ", comPort)
test = 0
try:
    serialPort = serial.Serial(port=comPort, baudrate=9600, timeout=0, parity=serial.PARITY_EVEN, stopbits=1)
    print("Connection Successful!")
    test = 1
except Exception as e:
    print("Connection Failed :(")
size = 1024
#serialPort2 = serial.Serial(port='COM6', baudrate=9600, timeout=0, parity=serial.PARITY_EVEN, stopbits=1)
while test:
    data = serialPort.readline(size)
    if data:
        print(data)