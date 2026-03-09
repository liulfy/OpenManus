

import numpy as np
from business_scene.haobai.hospital.department_match_with_embedding.embedding_save import department_names, department_vectors
from business_scene.haobai.hospital.text_embedding_v4 import get_text_embedding



def query_result(user_query = "骨科"):
    user_embedding = get_text_embedding(user_query)
    user_embedding = np.array(user_embedding)
    dot_result = department_vectors.dot(user_embedding)
    max_pos = np.argmax(dot_result)
    return department_names[max_pos] + str(100001 + max_pos)




