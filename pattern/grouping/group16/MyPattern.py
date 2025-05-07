import numpy as np
import pandas as pd
import os

def create_matrix(size, thickness):
    matrix = np.zeros((size, size), dtype=int)
    # 12以下正常縮
    if thickness <= 1:
        if thickness < size // 2:
            matrix[thickness:size-thickness, thickness:size-thickness] = 1 #外框補1
    # 12~22外框10，內框向外2後繼續縮
    elif thickness <= 3:
        thickness1 = 2
        if thickness1 < size // 2:
            matrix[thickness1:size-thickness1, thickness1:size-thickness1] = 1
        thickness -= 2
        if thickness < size // 2:
            matrix[thickness:size-thickness, thickness:size-thickness] = 0
     # 22以下外框10，中框18，外框再向外2(共4)後繼續縮
    else:
       thickness1 = 1
       if thickness1 < size // 2:
           matrix[thickness1:size-thickness1, thickness1:size-thickness1] = 1
       thickness2 = 2
       if thickness2 < size // 2:
           matrix[thickness2:size-thickness2, thickness2:size-thickness2] = 0
       thickness -= 4
       if thickness < size // 2:
           matrix[thickness:size-thickness, thickness:size-thickness] = 1
    return matrix

size = 8
current_directory = os.getcwd()

for thickness in range(20):
    matrix = create_matrix(size, thickness)
    inverted_matrix = 1 - matrix
    # copy 3 times to 128x128
    top = np.hstack((matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix))
    bottom = np.hstack((inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix))
    
    top1 = np.hstack((matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix,matrix, inverted_matrix))
    bottom1 = np.hstack((inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix,inverted_matrix, matrix))
    final_matrix = np.vstack((top, bottom,top1,bottom1,top, bottom,top1,bottom1,top, bottom,top1,bottom1,top, bottom,top1,bottom1))
    
    df = pd.DataFrame(final_matrix, dtype=int)
    file_path = os.path.join(current_directory, f'move{thickness}.csv')
    df.to_csv(file_path, index=False, header=False)
    
