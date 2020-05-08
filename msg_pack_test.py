import msgpack

data = {}
data["button"] = 5

packed = msgpack.packb(data)
print(packed)
print( ''.join(' {:02x}'.format(x) for x in packed))


unpack = msgpack.unpackb(packed)
print(unpack)


ppp = list()
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
unpack = msgpack.unpackb(packed)
print(unpack)


#a = "129, 166, 98, 117, 116, 116, 111, 110, 5"
a = "0x81,0xa6,0x62,0x75,0x74,0x74,0x6f,0x6e,0x05"
b = a.split(",")
a = bytearray()
for e in b:
    a.append(int(e))
a
print(a)

un_ = msgpack.unpackb(a)
print(un_)
