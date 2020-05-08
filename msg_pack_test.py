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