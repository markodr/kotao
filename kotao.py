import time
import dht
import socket
import network
import ure
import onewire, ds18x20
import machine
import utime
import network
import esp
from machine import Pin


'''
Izmerene vrednosti sa senzora
    V0 - Temperatura
    V1 - Vlaznost
    V4 - Temperatura vode u kotlu
Prekici za paljenje/gasenje senzora
    V2 - Prekidac PALI Grejanje
    V3 - Prekidac BLOKIRAJ Grejanje
Terminal
    V5 - Loguj custom exception
Eksterni API
    V9 - Thingspeak prikaz
LCD za prikaz vremena
    V10- LCD prvi red
    V11 - LCD drugi red
Skalirane vrednosti za prikaz
    V12 - Prikaz prekidaca BLOKIRAJ Grejanje
    V13 - Prikaz prekidaca PALI Grejanje
'''

# Dodati jedan buzzer prilikom zbog reseta, staviti ga na pwm pin
# PODESITI ONLINE STATUS
# But I already correct all the pins ( GPIO0 pulled up, GPIO15 pulled down,
# rst and ch_pc also pulled up) and the problem continues

def http_get(url):
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(1000)
        if data:
            #print('\nPrimljeno = ',len(data))
            #print(url)
            #print(str(data, 'utf8'), end='')
            # Zasto ovde radi return ?
            return data.decode('utf-8')
        else:
            break
    s.close()

esp.osdebug(None)
pauza = 60
excepions = 0

#wdt = machine.WDT(5000)
#wdt.feed()

# Definisano i u boot-u
taster_pali = Pin(5, Pin.OUT, Pin.PULL_UP)


# Sobni senzor
d = dht.DHT22(machine.Pin(4))

# Senzor vode kotla
dat = machine.Pin(13)
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds.scan()

# Da probam da uhvatim vreme za exceptions
vreme = 'x:x'

# %0A new line
# Ovde puca ako je losa konekcija


while (True):
    # Uokliko je pukla konekcija ispisi vreme na terminalu ovo mozda ne treba
    # if not sta_if.isconnected():
    #     print ('\nPukao je WiFi/konekcija proveri vreme na Blynk terminalu : ',vreme)
    print('\nPocetak Merenja')

#  ----- Ocitavanje DHT22 Senzora -----
    try:
        d.measure()
        temperatura=d.temperature()
        vlaznost=d.humidity()
        print ('          Temperatura : ', temperatura)
        print ('          Vlaznost    : ',vlaznost)
    except:
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V5?value=' + str(vreme) + '_Pukao_DHT22%0A')

#  ----- Ocitavanje DS1820 Senzora -----
    try:
        ds.convert_temp()
        time.sleep(1)
        for rom in roms:
            kotao_temperatura= ds.read_temp(rom)
            print( '          Temp. vode  : ', kotao_temperatura)
    except:
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V5?value=' + str(vreme) + '_Pukao_DS1820%0A')
    print ('Kraj Merenja\n')

# ----- UPDATE APLIKACIJE -----
    try:
# BLINK
    # Vlaznost prostorije - Update v1
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V1?value='+str(vlaznost))
        print('Vlaznost : Update OK')
    # Temperatura prostorije - Update v0
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V0?value='+str(temperatura))
        print('Temperatura : Update OK')
    # Temperatura vode u kotlu - v4
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V4?value='+str(int(kotao_temperatura)))
        print('Kotao : Update OK')
    # Preuzmi RTC format podataka Update v10,v11 utime.localtime http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc
        rtc_format = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/rtc')
        RTC_raw = ure.search('\[(\d+)]', rtc_format).group(1)
        formatirano_vreme = utime.localtime(int(RTC_raw))
        #print ('RTC je      : ', RTC_raw, '=',formatirano_vreme)
    # Ispisi Vreme - Datum poslednje konekcije 1-red v10 2-red v11
        datum = '___' + str( formatirano_vreme[1]) + '.' + str(formatirano_vreme[2]) + '.' + str(formatirano_vreme[0]-30)
        #print(type(datum), datum)
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V10?value=' + datum )
        # Dodajemo 0 zbog formata sekundi
        if (formatirano_vreme[5]<10):
            vreme = '____' +  str(formatirano_vreme[3]) + ':' + str(formatirano_vreme[4]) + ':' + '0' + str(formatirano_vreme[5])
        else:
            vreme = '____' +  str(formatirano_vreme[3]) + ':' + str(formatirano_vreme[4]) + ':' + str(formatirano_vreme[5])
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V11?value=' + vreme )
        print('RTC : Update OK')

    # Grejanje Taster PALI - Dowload/Update v2,v13 jebe regerx
        web_prekidac_pali = http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/get/V2')
        prekidac_pali = ure.search('\[.(\d).+\]', web_prekidac_pali).group(0)[2]
        http_get('http://blynk-cloud.com/15364b6f7e934f859ab8cc3803d2971b/update/V13?value='+str(prekidac_pali))
        #print( '\nRegex IZVADJENO    : ', smor)
        if (int(prekidac_pali) > 0):
            taster_pali.on()
            pass
        else:
            taster_pali.off()
        print('Prekidac Grejanje : Update OK')

    # ThingSpeak https://community.blynk.cc/t/help-with-webhook-and-thingspeak/8242/3
        http_get( 'https://api.thingspeak.com/update?api_key=J1T84N77WN3S33B8&field1=' + str(temperatura) + '&field2=' + str(kotao_temperatura)  + '&field3=' + str(kotao_temperatura) + '&field4=' + str(vlaznost))
        print('ThingSpeak : Update OK')
        # Resetujemo brojac za reset posto je sve proslo kako treba
        excepions=0
    except:
        # Valjalo bi resetovati ovde uredjaj posle n puta
        excepions = excepions + 1
        print('\nPukao je UPDATE tacno',excepions,'puta')

        if excepions >3:
            machine.reset()

        time.sleep(pauza)
        continue

    print ('\nCekam ',pauza,'sekundi\n')
    time.sleep(pauza)
