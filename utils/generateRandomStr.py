import random
import string

def generate_random_string(length):
    characters = string.ascii_letters + string.digits  # 包含字母和數字的字符集
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string