import random
from collections import Counter

def generate_compare_name_list(letters,n):

    # combinations = [a + b for a in letters for b in letters if a != b]
    combinations = [[a] + [b] for a in range(len(letters)) for b in range(len(letters)) if a != b]
    sample = random.sample(combinations,n)

    if n == 1:
        return sample
    else:
        # print(sample[0])
        while set(sample[0]) == set(sample[1]):
            sample = random.sample(combinations,n)
        return sample

# print(generate_compare_name_list('ABCD',2))