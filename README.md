# Modbus TCP Master Simulator Using QT for Python
This an implementation of a Modbus TCP master Simulator. This simulator allows reading Registers from a TCP Server. The Simulator is implemented with Qt for Python using the pyside6 Library. 
There are 4 Function codes implemented for reading Registers
1. Function code 0x01 for reading Coils
2. Function code 0x02 for reading Input registers
3. Function code 0x03 fpr reading holding registers
4. Function code 0x04 for reading input registers

This is Version 1 for the simulator. The Final Version of this simulator is intended to be able to read and write Modbus registers using both TCP and Serial (Modbus RTU).
With the current Implementation, you can only read Registers. 

Continous polling is not yet implemented so is done by sending a single read command using the read button.

### Instructions 
- Make sure you have python and pip installed. It is recommeded that you have python version 2.7 or higher
- Install dependencies in the requirements.txt file by running ```pip install -r requirements.txt``` command
- To configure you TCP server parameters, use the ```Settings``` menu
- Set the desired device id, function code and number of registers to read
- Press the ```connect``` button and then ```Read``` button to read data
