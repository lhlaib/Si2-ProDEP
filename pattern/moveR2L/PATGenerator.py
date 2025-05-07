NUM_ROW = 128
NUM_COLUMN = 128
Thickness = 7

for k in range(118):
    filename = "move" + str(k) +".csv"
    patfile = open(filename, 'w')
    for j in range(NUM_COLUMN):
        for i in range(NUM_ROW):
            if (i <= 2 or i >= 125 or j <= 2 or j >= 125):
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            else:
                if (i >= NUM_COLUMN - k - 3 and i <= NUM_COLUMN - k - 1):
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
