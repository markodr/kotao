# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import machine
import network

#import webrepl
#webrepl.start()
gc.collect()



def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('I9EBE', 'dTG7kKkAUJd4')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())


# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())
# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

# Definisem izlaz sa relejeom
taster_pali = machine.Pin(15, machine.Pin.OUT)

# Prilikom reseta ugasi grejanje_dugme
taster_pali.off()

# Povezi se na WiFi
do_connect()
