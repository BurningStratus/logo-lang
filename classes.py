from sys import _getframe
import re as regex

def __line__():
    return _getframe(1).f_lineno

class Iterator:
    def __init__(self, generator):
        self.element_count = 0
        self.empty = False
        self.next_element = None
        self.generator = generator
        try:
            self.next_element = next(self.generator)
        except StopIteration:
            self.empty = True

    def next(self):
        if self.empty: raise StopIteration()
        return_value = self.next_element
        try:
            self.next_element = next(self.generator)
        except StopIteration:
            self.next_element = None
            self.empty = True

        self.element_count += 1
        return return_value

    def peek(self):
        return self.next_element

class Logger:
    def __init__(self):
        self.write_log =False
    def log(self, params, fstring=None):
        if self.write_log:
            if fstring:
                print(f'LOG: {fstring}{params}')
            else:
                print(f'LOG: {params}')

class Debugger:
    def __init__(self):
        self.break_on_err =True

    def raise_error(self, message, code_ln=None):
        if self.break_on_err:
            breakpoint()

        line_list = regex.findall(r'^.*$', self.lexer.code) # split code into lines

        if code_ln and self.write_log:
            print(f"Error raised on line: {code_ln}")
        raise ValueError(
            f'Error:\t{message} at line {self.lexer.line}')
            #:\t\033[0;31m{line_list[self.lexer.line]}\033[0m')

class Stack:
    def __init__(self):
        self.stack = []
    def push(self, value):
        self.stack.append(value)
    def pop(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            return None
    def top(self):
        if len(self.stack) > 0:
            return self.stack[-1]
        else:
            return None

class Tokens:
    # this class is responsible for providing 
    # an iterator to spit out tokens

    #token 'None' should signify that the iterator is exhausted
    def __init__(self, token_list, loop=False):
        self.token_amt = 0
        self.ret_token = None # if None, then there is no tokens left
        self.loop = loop
        self.token_list = None
        self.token_feed = None
        self.set_iter(token_list) # set initial iterator
        if loop == True:
            self.token_list = token_list
    def set_iter(self, token_list):
        self.token_feed = Iterator(token_list)
    # get the next token in line
    def next_token(self):
        # if there is a returned token, use it
        if self.ret_token:
            token = self.ret_token
            self.ret_token = None
        else:
            try:
                token =self.token_feed.next()
            except StopIteration:
                # if loop is set, reset iterator
                if self.loop: 
                    self.set_iter(self.token_list)
                else:
                    token =None
        #endif

        self.token_amt += 1
        #print(f"TOKEN: .{token.value}::\t{token.type}.")
        return token
    def peek_token(self):
        # if there is a returned token, it will be taken next.
        if self.ret_token:
            return self.ret_token
        else:
            return self.token_feed.peek()
    def return_token(self, token):
        #print(f"returning {tk}")
        if self.ret_token:
            self.raise_error("Cannot return more than one token")
        self.done_return = True
        self.token_amt -= 1
        self.ret_token =token

class Token:
    def __init__(self, token_type, token_value, line, column):
        self.type = token_type # category of token
        self.value = token_value # value of the token
        self.line = line
        self.column = column
    def is_equal(self, other): # same as operator==() overload(you wish :/)
        return (other is Token and other.type == self.type and other.value == value)

class Procedure:
    def __init__(self, name, reference, *argv):
        self.local_env = None

        self.name = name
        # if a function has aliases, ref. points to the 'original' function
        self.reference = reference
        self.expected_args = []
        for arg in argv:
            self.expected_args.append(arg)
        self.arg_count = len(self.expected_args)

    def arg_type(arg, pos):
        # arg type checking 'any' is included
        if type(arg) == int or type(arg) == float:
            return 'number_literal'
        if type(arg) == str:
            return 'string_literal'

    def call(self, *argv):
        arg_vector = []
        for arg in argv:
            arg_vector.append(arg)
        arg_vector = arg_vector[::-1]
        self.reference(*arg_vector)

class Environment:
    def __init__(self, parent=None):
        self.variables = {}
        self.procedures = {}
        self.stack = Stack()
        self.parent = parent

    def get_env(self, name):
        if name in self.variables:
            return self.variables[name]
        elif name in self.procedures:
            return self.procedures[name].name
        else:
            return None

    def set_variable(self, name, value):
        self.variables[name] = value

    def set_procedure(self, name, handler):
        self.procedures[name] = handler

class Lexer:
    '''
    keywords = {
        'show',
        'print',
        'pd',
        'pendown',
        'down',
        'pu',
        'up',
        'penup',
        'forward',
        'fd',
        'backward',
        'bk',
        'right',
        'rt',
        'left',
        'lt',
        'setx',
        'sety',
        'setxy',
        'setpos',
        'goto',
        'setposition',
        'seth',
        'setheading',
        'home',
        'make',
        'repeat',
        'done',
        'mainloop',
        'stall',
        'sum'
        #'diff'      :self.sum_expressions_builtin,
        #'difference':self.sum_expressions_builtin,
    }
    '''
    def __init__(self, text, keywords_list):
        self.code = self.preprocessor(text)
        self.keywords = keywords_list

        self.char_pos = 0 # position in 'global' text
        self.line = 0 # number of parsed lines
        self.column = 0 # char position on the current line
        self.keywords = []
        self.token_spec = [
            ("argv_begin",      r'\('),     # start of argument vector
            ("argv_end",        r'\)'),     # end of args vector
            ("list",            r'[\[\]]'),     # end of the list
            # all strings are changed to string_literal later
            ("string_literal_terminated",       r'\"(.*?)"(?!\w+)'),
            ("string_literal_unterminated",     r'\"\w+(?=\s)'),
            ("number_literal",  r'\d+(\.\d*)?'),    # int or float
            #("list_begin",      r'\['),     # start of the list
            #("list_end",        r'\]'),     # end of the list
            ("operator",        r'[\+\-\*/%]'), # operator
            ("variable",        r':\w+'),   # variable
            ("identifier",      r'\w+'),    # names of procedures
            ("eol",             r'\n'),
        ]

        
    def preprocessor(self, text):
        # strip of whitespace
        text_f =regex.sub(r'#.*$', '', text, flags=regex.MULTILINE)
        #NOTE: do not delete empty lines
        #text_f =regex.sub(r'^\s*$\n?', '', text_f, flags=regex.MULTILINE)
        return text_f

    def tokens(self):
        # break down code into lines
        # parse the line for tokens
        # construct tokens into Token() objects
        # 'yield' these tokens

        # ig we dont have to split it into lines
        #line_list = regex.findall(r'^.*$', code) # split code into lines
        #for line in line_list:

        # straight up stolen from 
        # pyindex/re/Regular Expression Examples/Writing a tokenizer
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_spec)
        line_start = 0

        '''
        "string_literal"
        "number_literal"
        "list_begin",
        "list_end",
        "operator",
        "argv_begin",
        "argv_end",
        "variable",
        "identifier",
        "eol",
        '''

        for mo in regex.finditer(tok_regex, self.code, regex.MULTILINE):
            kind = mo.lastgroup
            value = mo.group()
            self.column = mo.start() - line_start 
            if kind == 'number_literal':
                value = float(value) if '.' in value else int(value)
            elif kind == 'string_literal_unterminated':
                value = regex.sub(r'[" ]', '', value)
                kind = 'string_literal'
            elif kind == 'string_literal_terminated':
                value = regex.sub(r'"', '', value)
                kind = 'string_literal'
            elif kind == 'identifier' and value in self.keywords:
                kind = value
            elif kind == 'variable':
                value = value.strip(':')
            elif kind == 'eol':
                line_start = mo.end()
                self.line += 1

            # NOTE: not implemented
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} unexpected on line {line_num}')

            yield Token(kind, value, self.line, self.column)
        #endfor

def test_lexer():
    l = Lexer('show "ech\nshow 10\n :e\n[ "echo " "bravo ]\n(show "echo "foxtrot)\n', ['show'])
    t = l.tokens()
    while True:
        try:
            tk = next(t)
            if tk.value == '\n': tk.value = tk.value.replace("\n","\\n")
            print(f'{tk.type}', f':{tk.value}.', sep='\t')
        except StopIteration:
            break

if __name__ == "__main__":
    print(">>> Calling Lexer independently")
    test_lexer()
    print(">>> END")

