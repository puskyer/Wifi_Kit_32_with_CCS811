
# for ESP-01S DHT11 v1.0
# TB:IOTMCU
import dht, time
import ubinascii
import machine
import micropython
from umqttsimple import MQTTClient
from machine import Pin

sensor = dht.DHT22(machine.Pin(26))
mqtt_server = '192.168.1.41'
mqtt_port = 1883
mqtt_user = 'mqttUser'
mqtt_password = 'MqttPass'
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = b'DHT11/notice'
topic_pub_temperature = b'DHT11/temperature'
topic_pub_humidity = b'DHT11/humidity'
keepalive = 0

last_message = 0
message_interval = 30
counter = 0


def sub_cb(topic, msg):
  print((topic, msg))      
  if topic == topic_sub and msg == b'restart':
    print('ESP received restart message')
    time.sleep(10)
    machine.reset()

def connect_and_subscribe():
  global client_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password, topic_sub
  client = MQTTClient(client_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password, keepalive)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker'% (mqtt_server))
  print('subscribed to %s topic' % (topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

#def blink_led():
#  Pin(led_pin, Pin.OUT).value(on)
#  time.sleep(1)
#  Pin(led_pin, Pin.OUT).value(off)    
#  print('LED blinked!')

try:
#  blink_led()
  client = connect_and_subscribe()
except OSError as e:
  print('First Connect ERROR!')
  restart_and_reconnect()

while True:
  try:
    client.check_msg()
#    print('Connect ERROR!')
    sensor.measure() 
    if (time.time() - last_message) > message_interval:
      client.publish(topic_pub_temperature, sensor.temperature())
      client.publish(topic_pub_humidity, sensor.humidity())
      last_message = time.time()
      #print ('publishing to topic %s' % (topic_pub))
      #print ('with message %s' % (msg))      
      #print ('last_message is %s' % (last_message))      
  except OSError as e:
    print('Second Connect ERROR!')
    restart_and_reconnect()
    

