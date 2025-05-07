NUM_ROW = 128
NUM_COLUMN = 128
Thickness = 2

for k in range(118):
    filename = "move" + str(k) +".csv"
    patfile = open(filename, 'w')
    for j in range(NUM_COLUMN):
        for i in range(NUM_ROW):
            if (i <= 2 or i >= 125 or j <= 2 or j >= 125):
            # if (i <= 7 or j <= 7 or j >= 120):
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            else:
                if (i >= k + 0 and i <= k + 2):
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
