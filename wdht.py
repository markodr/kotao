#https://forum.micropython.org/viewtopic.php?t=1392
from machine import enable_irq, disable_irq
import time

def getval(pin) :
    ms = [1]*300
    pin(0)
    time.sleep_us(20000)
    pin(1)
    irqf = disable_irq()
    for i in range(len(ms)):
        ms[i] = pin()      ## sample input and store value
    enable_irq(irqf)
    return ms

def decode(inp):
    res= [0]*5
    bits=[]
    ix = 0
    try:
        if inp[0] == 1 : ix = inp.index(0, ix) ## skip to first 0
        ix = inp.index(1,ix) ## skip first 0's to next 1
        ix = inp.index(0,ix) ## skip first 1's to next 0
        while len(bits) < len(res)*8 : ##need 5 * 8 bits :
            ix = inp.index(1,ix) ## index of next 1
            ie = inp.index(0,ix) ## nr of 1's = ie-ix
            bits.append(ie-ix)
            ix = ie
    except:
        return([0xff,0xff,0xff,0xff])

    for i in range(len(res)):
        for v in bits[i*8:(i+1)*8]:   #process next 8 bit
            res[i] = res[i]<<1  ##shift byte one place to left
            if v > 2:
                res[i] = res[i]+1  ##and add 1 if lsb is 1

    if (res[0]+res[1]+res[2]+res[3])&0xff != res[4] :   ##parity error!
        print("Checksum Error")
        res= [0xff,0xff,0xff,0xff]

    return(res[0:4])

def DHT11(pin):
    res = decode(getval(pin))
    temp = 10*res[0] + res[1]
    hum = 10 * res[2] + res[3]
    return temp, hum

def DHT22(pin) :
    res = decode(getval(pin))
    hum = res[0]*256+res[1]
    temp = res[2]*256 + res[3]
    if (temp > 0x7fff):
        temp = 0x8000 - temp
    return temp, hum
