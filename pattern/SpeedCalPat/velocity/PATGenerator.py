NUM_ROW = 128
NUM_COLUMN = 128
Thickness = 7

for k in range(13,20):
    filename = "move" + str(k) +".csv"
    patfile = open(filename, 'w')
    for j in range(NUM_COLUMN):
        for i in range(NUM_ROW):
            if (i >= 55 + k - 13 and i <= 56 + k - 13): # line
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            elif (i >= 76 - k + 13 and i <= 77 - k + 13): # line
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
