NUM_ROW = 128
NUM_COLUMN = 128
Thickness = 7

for k in range(0,1):
    filename = "move" + str(k) +".csv"
    patfile = open(filename, 'w')
    for j in range(NUM_COLUMN):
        for i in range(NUM_ROW):
            if (i >= 17 + k and i <= 18 + k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 23 - k and i <= 24 - k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 59 - k and i <= 60 - k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 65 - k and i <= 66 - k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 101 - k and i <= 102 - k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 107 - k and i <= 108 - k): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            else:
                if(i == NUM_COLUMN - 1):
                    patfile.write('0')
                else:
                    patfile.write('0, ')
        patfile.write('\n')
