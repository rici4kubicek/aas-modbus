import msgpack
import json

data = {}
data = json.loads("{\"button\": 5}")
packed = msgpack.packb(data)
print(packed)

print(''.join(' {:02x}'.format(x) for x in packed))
val_ascii = [ord(v) for v in "{\"button\": 5}"]
print(val_ascii)
print(''.join(' 0x{:02x}'.format(x) for x in val_ascii))

data = {}
data = json.loads("{ \"uid\": [ 136, 4, 106, 105, 143 ], \"tag\": { \"tag_vendor\": \"NXP\", \"user_memory_offset\": "
                  "4, \"tag_type\": \"NTAG213\", \"tag_protocol\": 3, \"tag_size\": 144 }, \"data\": [ [ 4, 106, 105, "
                  "143 ], [ 66, 236, 76, 129 ], [ 99, 72, 0, 0 ], [ 225, 16, 18, 0 ], [ 21, 22, 31, 32 ], [ 52, 3, 0, "
                  "254 ], [ 72, 138, 76, 76 ], [ 5, 3, 8, 10 ], [ 5, 3, 8, 10 ], [ 32, 59, 45, 41 ], [ 0, 0, 0, 0 ], "
                  "[ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 5, 3, 8, 10 ], [ 0, 0, 0, 0 ], "
                  "[ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], "
                  "[ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], "
                  "[ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], "
                  "[ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], [ 5, 3, 8, 10 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 189 ], "
                  "[ 21, 3, 8, 10 ], [ 0, 5, 0, 0 ], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ] ], \"read_state\": \"OK\", "
                  "\"timestamp\": 1583574457.57088 }")
print(data["data"][0])

print(data)
packed = msgpack.packb(data)
print(packed)
print( ''.join(' {:02x}'.format(x) for x in packed))


unpack = msgpack.unpackb(packed)
print(unpack)


ppp = bytearray()

ppp.append(0x81)
ppp.append(0xa6)
ppp.append(0x62)
ppp.append(0x75)
ppp.append(0x74)
ppp.append(0x74)
ppp.append(0x6f)
ppp.append(0x6e)
ppp.append(0x05)

print(ppp)
unpack2 = msgpack.unpackb(ppp)
print(unpack2)


a = "129, 166, 98, 117, 116, 116, 111, 110, 5"
#a = "0x81,0xa6,0x62,0x75,0x74,0x74,0x6f,0x6e,0x05"
b = a.split(",")
a = bytearray()
for e in b:
    a.append(int(e))
a
print(a)

un_ = msgpack.unpackb(a)
print(un_)
