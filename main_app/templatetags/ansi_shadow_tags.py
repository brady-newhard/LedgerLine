from django import template

register = template.Library()

def generate_ascii_banner(text):
    """
    Generates a simple ASCII art banner for text using standard ASCII characters
    that will display correctly in browsers.
    """
    text = text.upper()
    
    # Create a double-line border banner
    lines = []
    border_top = "+" + "-" * (len(text) + 6) + "+"
    border_bottom = "+" + "-" * (len(text) + 6) + "+"
    
    lines.append(border_top)
    lines.append("|   " + text + "   |")
    lines.append(border_bottom)
    
    return "\n".join(lines)

def generate_big_ascii_art(text):
    """
    Generate bigger ASCII art for titles - simplified version of FIGlet
    that works well in browsers.
    """
    text = text.upper()
    result = []
    
    for char in text:
        if char == ' ':
            result.append(['    ', '    ', '    ', '    ', '    '])
        else:
            result.append(get_big_char(char))
    
    # Transpose the result to create horizontal text
    lines = ['', '', '', '', '']
    for char_lines in result:
        for i, line in enumerate(char_lines):
            lines[i] += line
    
    return '\n'.join(lines)

def get_big_char(char):
    """Return the big ASCII representation of a character."""
    big_chars = {
        'A': [
            ' /\\ ',
            '/--\\',
            '/  \\',
            '    ',
            '    '
        ],
        'B': [
            '|-- ',
            '|--\\',
            '|__/',
            '    ',
            '    '
        ],
        'C': [
            ' -- ',
            '/   ',
            '\\__ ',
            '    ',
            '    '
        ],
        'D': [
            '|-- ',
            '|  \\',
            '|__/',
            '    ',
            '    '
        ],
        'E': [
            '|---',
            '|-- ',
            '|___',
            '    ',
            '    '
        ],
        'F': [
            '|---',
            '|-- ',
            '|   ',
            '    ',
            '    '
        ],
        'G': [
            ' -- ',
            '/  _',
            '\\__/',
            '    ',
            '    '
        ],
        'H': [
            '|  |',
            '|--|',
            '|  |',
            '    ',
            '    '
        ],
        'I': [
            '----',
            ' || ',
            '----',
            '    ',
            '    '
        ],
        'J': [
            '   |',
            '   |',
            '\\_/ ',
            '    ',
            '    '
        ],
        'K': [
            '|  /',
            '|-< ',
            '|  \\',
            '    ',
            '    '
        ],
        'L': [
            '|   ',
            '|   ',
            '|___',
            '    ',
            '    '
        ],
        'M': [
            '|\\  /|',
            '| \\/ |',
            '|    |',
            '      ',
            '      '
        ],
        'N': [
            '|\\  |',
            '| \\ |',
            '|  \\|',
            '     ',
            '     '
        ],
        'O': [
            ' -- ',
            '/  \\',
            '\\__/',
            '    ',
            '    '
        ],
        'P': [
            '|-- ',
            '|__\\',
            '|   ',
            '    ',
            '    '
        ],
        'Q': [
            ' -- ',
            '/  \\',
            '\\_\\_\\',
            '     ',
            '     '
        ],
        'R': [
            '|-- ',
            '|__/',
            '|  \\',
            '    ',
            '    '
        ],
        'S': [
            ' ---',
            ' __ ',
            '___/',
            '    ',
            '    '
        ],
        'T': [
            '----',
            ' || ',
            ' || ',
            '    ',
            '    '
        ],
        'U': [
            '|  |',
            '|  |',
            '\\__/',
            '    ',
            '    '
        ],
        'V': [
            '\\    /',
            ' \\  / ',
            '  \\/  ',
            '      ',
            '      '
        ],
        'W': [
            '|     |',
            '|  |  |',
            ' \\/ \\/ ',
            '       ',
            '       '
        ],
        'X': [
            '\\ / ',
            ' X  ',
            '/ \\ ',
            '    ',
            '    '
        ],
        'Y': [
            '\\ / ',
            ' |  ',
            ' |  ',
            '    ',
            '    '
        ],
        'Z': [
            '---/',
            ' / ',
            '/___',
            '    ',
            '    '
        ],
        '0': [
            ' -- ',
            '/  \\',
            '\\__/',
            '    ',
            '    '
        ],
        '1': [
            ' /| ',
            '  | ',
            ' _|_',
            '    ',
            '    '
        ],
        '2': [
            ' -- ',
            '  / ',
            ' /___',
            '     ',
            '     '
        ],
        '3': [
            '--- ',
            ' __|',
            '___/',
            '    ',
            '    '
        ],
        '4': [
            '|  |',
            '|__|',
            '   |',
            '    ',
            '    '
        ],
        '5': [
            '|---',
            '|__ ',
            '___|',
            '    ',
            '    '
        ],
        '6': [
            ' -- ',
            '/__ ',
            '\\__/',
            '    ',
            '    '
        ],
        '7': [
            '----',
            '   /',
            '  / ',
            '    ',
            '    '
        ],
        '8': [
            ' -- ',
            '|--|',
            '\\__/',
            '    ',
            '    '
        ],
        '9': [
            ' -- ',
            '\\__|',
            ' __/',
            '    ',
            '    '
        ],
        ':': [
            ' ',
            'o',
            'o',
            ' ',
            ' '
        ],
        '.': [
            '  ',
            '  ',
            'o ',
            '  ',
            '  '
        ],
        ',': [
            '  ',
            '  ',
            'o ',
            '/ ',
            '  '
        ],
        '-': [
            '    ',
            '----',
            '    ',
            '    ',
            '    '
        ],
        '_': [
            '     ',
            '     ',
            '_____',
            '     ',
            '     '
        ],
        '!': [
            '| ',
            '| ',
            'o ',
            '  ',
            '  '
        ],
        '?': [
            ' -- ',
            '   /',
            '  o ',
            '    ',
            '    '
        ],
        '(': [
            ' /',
            '| ',
            ' \\',
            '  ',
            '  '
        ],
        ')': [
            '\\ ',
            ' |',
            '/ ',
            '  ',
            '  '
        ],
        '/': [
            '  /',
            ' / ',
            '/  ',
            '   ',
            '   '
        ],
        '\\': [
            '\\  ',
            ' \\ ',
            '  \\',
            '   ',
            '   '
        ],
    }
    
    # Default character for unsupported symbols
    return big_chars.get(char, [' ? ', ' ? ', ' ? ', '   ', '   '])

@register.simple_tag
def ansi_shadow(text):
    """
    Creates an ASCII art banner for the given text.
    """
    return generate_big_ascii_art(text)