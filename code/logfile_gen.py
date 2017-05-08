f = open("logfilev2", "w")

for i in range(0, 10):
    f.write(str(0))
    f.write(str(0))
    f.write(str(0))
    f.write(str(i))
    for j in range(1, 37):
        f.write(str(0))

for i in range(10, 100):
    f.write(str(0))
    f.write(str(0))
    f.write(str(i))
    for j in range(1, 37):
        f.write(str(0))

for i in range(100, 1000):
    f.write(str(0))
    f.write(str(i))
    for j in range(1, 37):
        f.write(str(0))

for i in range(1000, 1024):
    f.write(str(i))
    for j in range(1, 37):
        f.write(str(0))

for i in range(0, 1024):
    f.write("{0} {1}\n".format(str(i), str(i)))

f.close()
        
