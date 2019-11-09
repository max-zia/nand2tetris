"""
Allows ' '.join(array) to be used in such a way that punctuation markings are
not preceded by spaces.
"""
def join_punctuation(seq, characters='.,?!:'):
    characters = set(characters)
    seq = iter(seq)
    current = next(seq)

    for nxt in seq:
        if nxt in characters:
            current += nxt
        else:
            yield current
            current = nxt

    yield current

"""
Collapses string constants which appear over several indices into a single
indices. Also removes the quotation marks surrounding string constant. 
"""
def collapse_string_constants(tokens):
    indices = ['placeholder']
    while len(indices) > 0:
        indices = [i for i, j in enumerate(tokens) if j == '"']

        # Concatenate string tokens between quotation mark tokens
        temp = []
        tokens[indices[0]] = ''
        for j in range(indices[0] + 1, indices[1]):
            temp.append(tokens[j])
        tokens[indices[0]] = '"' + ' '.join(join_punctuation(temp)) + '"'

        # Delete redunant tokens
        for j in range(indices[0] + 1, indices[1] + 1):
            del tokens[indices[0] + 1]
        
        # Delete pair of indices from indices to progress
        del indices[0]
        del indices[0]
