f = open("zero", "w")

for i in range(0, 1024):
    f.write(str(i))
    for j in range(0, 40):
        f.write(str(0))

f.close()
        
