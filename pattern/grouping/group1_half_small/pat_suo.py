import numpy as np
import pandas as pd
import os

def write_file(file_name, mat):
    fo = open(file_name, 'w')
    d = {0: '0', 1: '1'}
    for i in range(128):
        for j in range(128):
            fo.write(d[mat[i, j]])
            fo.write(',' if j < 127 else '\n')
    fo.close()

def create_matrix(size, thickness):
    matrix = np.zeros((size, size), dtype=int)
    for i in range(size):
        for j in range(size):
            if abs(i - size / 2) + abs(j - size / 2) <= thickness:
                try:
                    matrix[i][j] = 1
                except IndexError:
                    pass 

    return matrix

size = 128
current_directory = os.getcwd()

idx = 0
for thickness in range(35):
    matrix = create_matrix(size, 48 - thickness)
    for i in range(4):
        matrix[:, i] = 1
        matrix[i, :] = 1
        matrix[:, 127-i] = 1
        matrix[127-i, :] = 1
    write_file('move%d.csv' % idx, matrix)
    idx += 1