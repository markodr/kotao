import esp
import time
import machine
import dht
import socket
import network


def http_get(url):
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(100)
        if data:
            print(str(data, 'utf8'), end='')
        else:
            break
    s.close()


# Definisanje modula
esp.osdebug(None)
pin = machine.Pin(0, machine.Pin.OUT)
d = dht.DHT11(machine.Pin(4))
adc = machine.ADC(0)

# Potrebne promenljive
grejanje_dugme=0

# Zabrana AP
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
print ('\nAccess Point = ' , ap_if.active())

# Dozvola stanice
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print ('Stanica = ', sta_if.active() )

# Povezivanje na ruter
print ('Povezani smo = ', sta_if.isconnected() )
if (  sta_if.isconnected() is not True ):
    sta_if.connect('I9EBE','dTG7kKkAUJd4')
print( '\nI9EBE', sta_if.ifconfig() )

while (True):
    time.sleep(10)
# Pocetak akvizicije - 15364b6f7e934f859ab8cc3803d2971b
    pin.off()
    print('\nStart Merenja\n')
    merenje= d.measure()
    temperatura=d.temperature()
    vlaznost=d.humidity()
    print ('Merenje',merenje)
    print ('Temperatura', temperatura)
    print ('Vlaznost',vlaznost)
    print('\nKraj Merenja\n')

# Vlaznost
    vlaznost_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V1?value='+str(vlaznost)
    http_get(vlaznost_link)
# Temperatura
    temperatura_link = 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V0?value='+str(temperatura)
    http_get(temperatura_link)
'''
# Grejanje Taster
#    grejanje_link= 'http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2'
#    http_get(grejanje_link)
'''
