# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import machine
#import webrepl
#webrepl.start()
gc.collect()

# Ovde gasim pinove posto nakon reseta idu na .on()
taster_pali = machine.Pin(2, machine.Pin.OUT)
taster_odblokiraj = machine.Pin(15, machine.Pin.OUT)

# Prilikom reseta ugasi grejanje_dugme
taster_pali.off()
taster_odblokiraj.off()
