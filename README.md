##Modbus TCP Plugin for Smarthome.py 
##modbus_tcp

The Plugin is based on Smarthome.py for Communikate with a Wago/Beckhoff.. PLC.
It Read/Writes cyclical all used Registers(Items) to the PLC.
It is easy to use, like the Knx Plugin.
The Plugin is based on pymodbus, which you can found under:
https://github.com/bashwork/pymodbus

##[plugin.conf]
<pre>
[modbus]
	class_name = modbus
	class_path = plugins.modbus
	device = 192.168.178.24		#IP adress of Modbus device
	port = 502 			#standart 502 for Modbus
	timeout = 1000 			#ms
	cycle = 2			#s
	pe_adress = 0			#start of input Registers
	pe_length = 16 			#length of the input registers
	pa_adress = 16384		#start of output Registers
	pa_length = 16	        	#length of the ouput registers
</pre>


for example:
##[item.conf]
<pre>
[beckhoff]
	name = Beckhoff PLC
    	[[outputs]]
    	name = outputs
		[[[light]]]
		name = light
		type = bool
		visu = yes
		visu_acl = rw
		modbus_on = 1
		modbus_type = bool
		modbus_byte = 16384
		modbus_bit = 0          #position in an 16bit string 16<-0
		modbus_dpt = 1
</pre>
