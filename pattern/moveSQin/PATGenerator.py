NUM_ROW = 128
NUM_COLUMN = 128
Thickness = 7

for k in range(118):
    filename = "move" + str(k) +".csv"
    patfile = open(filename, 'w')
    for j in range(NUM_COLUMN):
        for i in range(NUM_ROW):
            if (i <= k or i >= 127 - k or j <= k or j >= 127 - k):
                if(i == NUM_COLUMN - 1):
                    patfile.write('1')
                else:
                    patfile.write('1, ')
            # else:
            #     if (i >= NUM_COLUMN - k - 5 and i <= NUM_COLUMN - k - 4):
            #         if(i == NUM_COLUMN - 1):
            #             patfile.write('1')
            #         else:
            #             patfile.write('1, ')
            else:
                if(i == NUM_COLUMN - 1):
                    patfile.write('0')
                else:
                    patfile.write('0, ')
        patfile.write('\n')
