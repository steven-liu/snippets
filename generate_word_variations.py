import itertools


def generate_variations(template_str, replace_with_chars):
    """Generate variations of a string with certain characters substituted.

    All instances of the '*' character in the template_str parameter are
    substituted by characters from the replace_with_chars string. This function
    generates the entire set of possible permutations."""

    count = template_str.count('*')
    _template_str = template_str.replace('*', '{}')

    variations = []
    for element in itertools.product(*itertools.repeat(list(replace_with_chars), count)):
        variations.append(_template_str.format(*element))

    return variations


if __name__ == '__main__':

    # use this set to test
    REPLACE_CHARS = '!@#$%^&*'

    # excuse the bad language...
    a = generate_variations('sh*t', REPLACE_CHARS)
    b = generate_variations('s**t', REPLACE_CHARS)
    c = generate_variations('s***', REPLACE_CHARS)
    d = generate_variations('f*ck', REPLACE_CHARS)
    e = generate_variations('f**k', REPLACE_CHARS)
    f = generate_variations('f***', REPLACE_CHARS)

    print list(set(a+b+c+d+e+f))
