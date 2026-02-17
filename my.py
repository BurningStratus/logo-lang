#!/sbin/python
import operator
import re as regex
import turtle as t
from sys import argv, _getframe

# NOTE to self: avoid adding own features cuz 
#               they might break the official LOGO logic

# TODO: change move functions to use 
#       single_arg_builtin, double_arg_builtin and va_list_builtin
#       according to the number of args provided


# TODO: Changed the part with while true -> parse_expressions, 
# so now I need to change all builtins to use tokens instead of stack :/


def __line__():
    return _getframe(1).f_lineno


class Logger:
    def __init__(self):
        self.write_log =False
    def log(self, params, fstring=None):
        if self.write_log:
            if fstring:
                print(f'LOG: {fstring}{params}')
            else:
                print(f'LOG: {params}')


#https://www.calormen.com/jslogo/language.html
class Logo(Logger):
    def __init__(self, text=None, t=None):
        self.t  =t.Turtle()

        self.label_dict = {
            "__start___": 0
        }

        self.code       =self.preprocessor(text)
        self.line_nr    =0

        #self.process_labels() NOTE: rm

        self.returned_token =None
        self.stack =[]
        self.ret_addr =0

        self.variable_dict = {}

        self.token_feed =self.tokens()

        self.dispatch_operator = {
            '+': operator.add,
            #'-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }

        self.dispatch_builtin ={
            'show'      :self.show_builtin,
            'print'     :self.show_builtin,
            #'jmp'       :self.jump_builtin, # NOTE: NOT IN REF.MAN.
            'pd'        :self.t.pendown,
            'pendown'   :self.t.pendown,
            'down'      :self.t.pendown,
            'pu'        :self.t.penup,
            'up'        :self.t.penup,
            'penup'     :self.t.penup,
            'done'      :self.t.screen.mainloop,
            'mainloop'  :self.t.screen.mainloop, #NOTE: NOT IN REF.MAN.
            'stall'     :self.t.screen.mainloop, #NOTE: NOT IN REF.MAN.
            'ret'       :self.call_ret_sr_builtin, #NOTE: NOT IN REF.MAN.
            'return'    :self.call_ret_sr_builtin, #NOTE: NOT IN REF.MAN
            'make'      :self.make_variable_builtin,

            #'call'      :self.call_sr_builtin,   #NOTE: NOT IN REF.MAN.
            # TODO: Move specific cmds like 'sum' to a different place
            # to make it possible to:
            # show sum 10 10
            # show sum 10 [ 11 12 34 11 ]
        }

        self.subcommand_builtin ={
            'sum'       :self.sum_expressions_builtin,
        }

        # TODO: bind to handler and exec from there
        # can use something like this vvvv
        # method_name = "__name__attribute_of_a_function"
        # method = getattr(object, method_name)
        # method()  # This will call the method

        self.dispatch_move_cmd ={
            'forward'   :self.t.forward,
            'backward'  :self.t.backward,
            'right'     :self.t.right,
            'left'      :self.t.left,
            'setx'      :self.t.setx,
            'sety'      :self.t.sety,
            'seth'      :self.t.setheading,
            'setheading':self.t.setheading,
            'setpos'    :self.setposition_move_builtin,
            'goto'      :self.setposition_move_builtin,
            'setposition':self.setposition_move_builtin,
        }
        # dictionary is a list of all supported commands
        self.dictionary = list(self.dispatch_builtin.keys())+\
            list(self.dispatch_move_cmd.keys())+\
            list(self.subcommand_builtin.keys())
    
    # strip of whitespace
    def preprocessor(self, text):
        text_f =regex.sub(r'#.*$', '', text, flags=regex.MULTILINE)
        text_f =regex.sub(r'^\s*$\n?', '', text_f, flags=regex.MULTILINE)
        return text_f

    def pushs(self, arg):
        if self.stack is None:
            self.stack = []
        self.stack.append(arg)
        self.log(self.stack,"STACK CONTENTS:")

    def pops(self):
        self.log(self.stack, "POP:")
        if self.stack is not None and len(self.stack) > 0:
            return self.stack.pop()
        else:
            return None

    def raise_error(self, message, code_ln=None):
        if code_ln and self.write_log:
            print(f"Error raised on line: {code_ln}")
        raise ValueError(
            f'Error:\t{message} \
            \n{self.line_nr}:\t\033[0;31m{self.code[self.line_nr]}\033[0m')

    '''
    def process_labels(self):
        line_number =0
        # search for and add all labels to dictionary

        while line_number < len(self.code):
            # add labels to a dictionary and continue parsing
            tmpstring =self.code[line_number].strip()
            if tmpstring[-1] ==":":
                # add only a name of the label
                self.label_dict[tmpstring.strip(" :")] =line_number
            line_number += 1
    '''

##TOKENIZING###################################################################

    def tokens(self):
        self.code =self.code.strip().split('\n')

        while self.line_nr < len(self.code):
            self.log(self.line_nr, "LINE:")

            for token in self.code[self.line_nr].split(' '):

                if token in self.dictionary or token in self.subcommand_builtin:
                    yield (token,)
                
                # NOTE: zalipuha!!!
                elif len(token) == 1 and token in "+-*/()[]=":
                    yield ('op',token)

                # TODO: this vvv 
                #elif token in "[]":
                #    yield ('list',token)

                elif token[0] == ":":
                    yield ("variable",token[1:])

                # zalipuha
                elif token.isnumeric() or token[1:].isnumeric():
                    yield ("number", int(token))

                #elif token.isalpha():
                elif token[0] == "\"":
                    yield ("string", str(token[1:]))

                # NOTE: LABELS MIGHT HAVE TO BE REMOVED :/
                #elif token.strip(":") in self.label_dict:
                #    continue
                    #yield ("label", str(token[:-1]))

                elif not token:
                    continue

                else:
                    self.raise_error(f'Syntax Error: Invalid token "{token}"')

            yield ('\n',)
            self.line_nr += 1

    # get the next token in line
    def ntok(self):
        # if there is a returned_token, use it
        if self.returned_token:
            tk =self.returned_token
            self.returned_token =None
        # else just advance to the next token
        else:
            try:
                tk =next(self.token_feed)
            except StopIteration:
                tk =None

        return tk

    # return the token
    def rtok(self, tk):
        #print(f"returning {tk}")
        if self.returned_token is not None:
            self.raise_error("Cannot return more than one token")
        self.returned_token =tk

##TOKENIZING###################################################################

##PARSE PROCESS################################################################
    # start the parsing process
    def parse_program(self):
        if not self.parse_statement():
            self.raise_error('Expected: statement')

        token =self.ntok()
        while token is not None:
            self.rtok(token)

            if not self.parse_statement():
                self.raise_error('Expected: statement')

            token =self.ntok()

        return True

    def parse_statement(self):
        #breakpoint()
        if not self.parse_builtin_dictionary() \
            and not self.parse_expression() \
            and not self.parse_expression_statement():
                self.raise_error('Unknown statement')

        #if not self.parse_print_statement() \
        #    and not self.parse_expression_statement() \
        #    and not self.parse_move_statement():
        #        self.raise_error('Unknown statement')
        #self.rtok(token)
        token=self.ntok()

        if token[0] != '\n':
            #breakpoint()
            self.raise_error('Expected: end of line')
        return True

    def parse_expression(self):
        # and token[0] not in self.subcommand_builtin:
        token =self.ntok()

        if token[0] !='number'\
          and token[0] !='string'\
          and token[0] !='variable'\
          and token[0] !='label'\
          and token[0] not in self.subcommand_builtin:
            #breakpoint()
            self.rtok(token)
            return False
        
        if token[0] == 'variable':
            if token[1] in self.variable_dict:
                self.pushs(self.variable_dict[token[1]])
            else:
                self.raise_error("Unknown variable name")

        elif token[0] in self.subcommand_builtin:
            # exec subcommand
            self.subcommand_builtin[token[0]]()

        elif token[0] != 'label':
            self.pushs(token[1])


        #TODO: make math expr handler here
        #maybe make a stack for calculations, 
        #where all nums and op:s will be pushed from the same line
        #to make it possible to implement operator precedence

        #calcvalue =self.math_expr()

        return True

    def parse_expression_statement(self):
        token =self.ntok()
        if token != ('op','['):
            self.rtok(token)
            return False

        while True: 
            token =self.ntok()

            if token[1] != "]": # end of array
                if token[0] == 'variable':
                    # dereference variable and check its existance
                    if token[1] in self.variable_dict:
                        self.pushs(self.variable_dict[token[1]])
                        continue
                    else:
                        self.raise_error("Unknown variable name")

                else:
                    # if not var, just push value to stack
                    self.pushs(token[1])
            # if ] is encountered, break out of the loooop
            else:
                break

        return True

    def math_expr(self):
        prv, nxt, ths, value =0,0,0,0
        self.pops() # remove the )
        tmpstack = []

        # TODO: operator precedence
        while self.stack[-1] != '(':
            tmpstack.append(self.pops())

        while len(tmpstack) >= 3:
            nxt =tmpstack.pop() # 2
            ths =tmpstack.pop() # +
            prv =tmpstack.pop() # 2

            if ths == '-':
                prv = -prv
                ths = '+'
            #print(tmpstack)
            #print(f"p:{prv} n:{nxt} t:{ths}")

            if type(nxt) == str and nxt in '+-':
            #it looks like this :   p:+  n:- t:2
            #it should look like:   p:-2 n:  t:+
                tmp_t =ths
                tmp_p =prv
                ths =tmp_p
                prv =int(f"{nxt}{tmp_t}")
                nxt =tmpstack.pop()
                
            tmpstack.append(self.dispatch_operator[ths](prv, nxt))

        #print(tmpstack)
        # end of expr, remove the (
        cval =self.pops()
        self.pushs(tmpstack.pop())

        return True

    def parse_builtin_dictionary(self):
        # NOTE: should execute both move cmds and other builtins
    
        token =self.ntok()
        #if token[0] not in self.dispatch_builtin:
        if token[0] not in self.dispatch_builtin \
            and token[0] not in self.dispatch_move_cmd:
            self.rtok(token)
            self.log(token, "token was returned in parse_builtin:")
            return False

        ### TODO: this part is needed, but need to find a way to add it

        #while self.parse_expression() or self.parse_expression_statement():
        #    pass

        if token[0] in self.dispatch_move_cmd:
            self.dispatch_move_cmd[token[0]]()
        else:
            self.dispatch_builtin[token[0]]()
        return True

##PARSE PROCESS################################################################

##BUILTIN HANDLERS#############################################################
    def single_arg_builtin(self):
        return True

    def double_arg_builtin(self):
        return True

    def va_list_builtin(self):
        return True
    
    def show_builtin(self):
        ### TODO: redo to make it work like official ref.
        # show [ foo bar char ] << sq. brackets signify va_list
        # show foo << no brackets mean only one arg

        if not self.parse_expression()\
            and not self.parse_expression_statement():
            self.raise_error('Expected: expression')

        if len(self.stack) > 1:
            self.stack = self.stack[::-1]

        i = 0
        while True:
            i =self.pops()
            if i is None:
                break

            print(i, end=" ")
            if len(self.stack) == 0:
                print()

        if len(self.stack) > 1:
            self.stack = self.stack[::-1]
        return True

    def jump_builtin(self):
        ln = self.pops()
        if ln is None:
            self.raise_error("Expected: address of the label")

        if type(ln) == int or ln.isnumeric():
            self.line_nr = ln
            return True

        if ln not in self.label_dict:
            self.raise_error("Invalid label")

        self.line_nr = self.label_dict[ln]
        return True

    def call_sr_builtin(self):
        self.ret_addr =self.line_nr
        self.jump_builtin()
        return True

    def call_ret_sr_builtin(self):
        
        if not self.ret_addr:
            return False

        self.line_nr= self.ret_addr
        return True

    def setposition_move_builtin(self):
        if not self.parse_expression() and not self.parse_expression_statement():
            self.raise_error('Expected: expression')
        
        if xcoord is None:
            self.raise_error("Expected: expression", __line__())

        ycoord =self.pops()
        if ycoord is None:
            ycoord=self.t.pos()[1]

        self.t.setposition(xcoord, ycoord)
        return True

    def make_variable_builtin(self):
        #breakpoint()
        token1 =self.ntok()
        token0 =self.ntok()

        if token1[0] != 'string':
            self.raise_error("Expected: name of the variable")

        if token0 is None:
            self.raise_error("Expected: expression")

        breakpoint()
        self.variable_dict[token1[1]] =token0[1]
        return True

    def sum_expressions_builtin(self):
        token1 =self.ntok()
        token0 =self.ntok()

        if token0[0] != 'number' or token1[0] != 'number':
            self.raise_error("Expected: expression")

        expr_1 =token0[1]
        expr_0 =token1[1]

        if expr_0 is None or expr_1 is None:
            self.raise_error("Expected: expression", __line__())

        # if variable
        if expr_0 in self.variable_dict:
            if type(self.variable_dict[expr_0]) == type(expr_1):
                self.variable_dict[expr_0] += expr_1
                return True
            # if variable and operand types dont match
            elif type(self.variable_dict[expr_0]) != type(expr_1):
                # cast to string if first operand is a string
                if type(self.variable_dict[expr_0]) is str:
                    self.variable_dict[expr_0] += str(expr_1)
                    return True

                elif type(expr_1) is str:
                    self.raise_error("Can not sum different types")

        # handle differences in types
        if type(expr_0) != type(expr_1):
            # cast to string if first operand is a string
            if type(expr_0) is str:
                self.pushs(expr_0 + str(expr_1))
                return True

            elif type(expr_1) is str:
                self.raise_error("Cannot concatenate int and string")
                
        else:
            self.pushs(expr_0 + expr_1)
            return True
        

##BUILTIN HANDLERS#############################################################
    def run(self):
        try:
            return self.parse_program()
        except ValueError as exc:
            print(str(exc))
            return False



if __name__ == "__main__":
    if len(argv) < 2:
        raise Exception("no input file")

    with open(argv[1], 'r') as fd:
        text =fd.read()

    lexer   =Logo(text,t)
    lexer.write_log =False
    lexer.run()

