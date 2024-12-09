import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import lib.card.card_io as card

def newData(ch0,ch1):
    print("{} data received on ch0 - {} data received on ch1".format(len(ch0),len(ch1)))

if __name__ == '__main__':
    ports = card.listSerialPort()
    for p in ports:
        print(p.manufacturer)
        print(p.description)
        if p.vid and p.vid==1155:
            if p.pid and  p.pid==22336:
                if (not p.location) | ("x.0" in p.location):
                    print("dev 1: {}".format(p.device))
                if (p.location):
                    if ("x.2" in p.location):
                        port = p
                        print("dev 2: {}".format(p.device))

    # myCard = card.cardAcqui( port.device,card.FREQUENCY_100HZ,card.NO_FILTER )
    # myCard.setDataReadyCB( newData )
    # print(ports)
    # port = card.findSerialPort()
    # print("Connecting to PORT {}".format(port))
    # if (not port):
    #     exit(1)

    # myCard = card.cardIO( port )
    # # myCard.runClient()
    # myCard.setConfigAvailableCB( config )

    run = True
    print("return empty string to close the connection")
    while (run):
        str = input(">>> ")
        if len(str)==0:
            run = False
        else:
            # if (str=='9'):
            #     myCard.askConfig()
            # if (str=='2'):
            #     myCard.setConfig({'PPG': 1, 'EMG': 0, 'GBF': 0, 'IMU': 0, 'samplingFreq': 50})
            # if (str=='3'):
            #     myCard.setConfig({'PPG': 1, 'EMG': 0, 'GBF': 0, 'IMU': 0, 'samplingFreq': 25})
            # if (str=='4'):
            #     myCard.setConfig({'PPG': 1, 'EMG': 0, 'GBF': 0, 'IMU': 0, 'samplingFreq': 100})
            # if (str=='1'):
            #     myCard.startAcqui()
            if (str=='0'):
                myCard.stopCard()
                run = False

    # myCard.stopClient()
