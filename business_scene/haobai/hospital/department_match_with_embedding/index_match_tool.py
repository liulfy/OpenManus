
from app.logger import logger
import numpy as np
from business_scene.haobai.hospital.department_match_with_embedding.embedding_save import number_map, department_names, department_vectors
from business_scene.haobai.hospital.text_embedding_v4 import get_text_embedding



def query_result(user_query = "骨科"):
    user_embedding = get_text_embedding(user_query)
    user_embedding = np.array(user_embedding)
    dot_result = department_vectors.dot(user_embedding)
    max_pos = np.argmax(dot_result)
    department_name = department_names[max_pos]
    department_number = number_map[department_name]
    logger.info(f'查询的结果为：{department_name + "  " + department_number}')
    return department_number


