#!/sbin/python

# NOTE: maybe I should reorient the project to use BASIC syntax?
# or even start all over again in C++?

# NOTE: bind to handler and exec from there
# can use something like this vvvv
# method_name = "__name__attribute_of_a_function"
# method = getattr(object, method_name)
# method()  # This will call the method

# NOTE: data types in logo:
# Word:      A string of characters (often representing numbers as well)
# Number: Just a word composed of digits
# List: A collection of words, lists, or arrays
# Array: Indexed collection, can be multi-dimensional, mutable
# Predicate Functions: Test data types, e.g., `wordp`, `listp`, `numberp`, `arrayp`
# Data Operations: Constructors (`word`, `list`, `sentence`) 
#   and mutators/selectors (`item`, `setitem`, etc.)
# Queries: Functions like `count`, `ascii`, `char`, `uppercase`, etc.


# TODO: current 'model' executes tokens just when it encounters them. 
# It should parse the line till the end first and make an execution stack of some sort


import operator
import re as regex
import turtle as t
from sys import argv

# custom headers
from classes import Iterator, Logger, Debugger
from classes import Environment, Stack
from classes import Token, Tokens, Procedure, Lexer

#https://www.calormen.com/jslogo/language.html
class Logo(Logger, Debugger):
    def __init__(self, text=None, t=None):
        self.t = t.Turtle()

        self.base_env = Environment()
        # create and register a new procedure in global env
        self.base_env.set_procedure("show", Procedure("show", self.show_builtin))
        self.base_env.set_procedure("print", Procedure("print", self.print_builtin))
        '''
        self.builtins ={
            'show'      :Procedure("show", self.show_builtin),
            'print'     :self.print_builtin,
            'pd'        :va_list_exec_t(self.t.pendown),
            'pendown'   :va_list_exec_t(self.t.pendown),
            'down'      :va_list_exec_t(self.t.pendown),
            'pu'        :va_list_exec_t(self.t.penup),
            'up'        :va_list_exec_t(self.t.penup),
            'penup'     :va_list_exec_t(self.t.penup),
            'forward'   :va_list_exec_t(self.t.forward,["number_literal"]),
            'fd'        :va_list_exec_t(self.t.forward,["number_literal"]),
            'backward'  :va_list_exec_t(self.t.backward,["number_literal"]),
            'bk'        :va_list_exec_t(self.t.backward,["number_literal"]),
            'right'     :va_list_exec_t(self.t.right,["number_literal"]),
            'rt'        :va_list_exec_t(self.t.right,["number_literal"]),
            'left'      :va_list_exec_t(self.t.left,["number_literal"]),
            'lt'        :va_list_exec_t(self.t.left,["number_literal"]),
            'setx'      :va_list_exec_t(self.t.setx,["number_literal"]),
            'sety'      :va_list_exec_t(self.t.sety,["number_literal"]),
            'setxy'     :va_list_exec_t(self.t.setposition,["number_literal","number_literal"]),
            'setpos'    :va_list_exec_t(self.t.setposition,["number_literal","number_literal"]),
            'goto'      :va_list_exec_t(self.t.setposition,["number_literal","number_literal"]),
            'setposition':va_list_exec_t(self.t.setposition,["number_literal","number_literal"]),
            'seth'      :va_list_exec_t(self.t.setheading,["number_literal"]),
            'setheading':va_list_exec_t(self.t.setheading,["number_literal"]),
            'home'      :va_list_exec_t(self.t.home),

            'make'      :self.make_variable_builtin,
            'repeat'    :self.repeat_builtin,

            'done'      :va_list_exec_t(self.t.screen.mainloop), #NOTE: NOT IN REF.MAN.
            'mainloop'  :va_list_exec_t(self.t.screen.mainloop), #NOTE: NOT IN REF.MAN.
            'stall'     :va_list_exec_t(self.t.screen.mainloop), #NOTE: NOT IN REF.MAN.
        }
        self.subcommands ={
            'sum'       :self.sum_expressions_builtin,
            #'diff'      :self.sum_expressions_builtin,
            #'difference':self.sum_expressions_builtin,
        }
        '''
        # dictionary is a list of all supported commands
        #self.builtin_dictionary = list(self.builtins.keys())

        #self.dictionary = self.builtin_dictionary+list(self.subcommands.keys())
        self.dictionary = list(self.base_env.procedures.keys()) # NOTE: newer
        self.builtin_dictionary = list(self.base_env.procedures.keys())

        # lexer takes the code and keyword list
        self.lexer = Lexer(text, self.dictionary)
        self.tokenizer = Tokens(self.lexer.tokens())
        self.call_stack = Stack()
        self.stack = Stack()

        self.write_log  = False
        self.break_on_err = False

        self.next_token = self.tokenizer.next_token # zalipuha !
        self.peek_token = self.tokenizer.peek_token # zalipuha !
        self.return_token = self.tokenizer.return_token # zalipuha !
    
    """
    def stack_push(self, arg, stack=None):
        # pass by reference is a bit complicated in python
        stack_snapshot =None
        if stack is not None:
            stack_snapshot = self.stack
            self.stack = stack

        self.stack.append(arg)
        self.log(stack,"STACK CONTENTS:")
        if stack_snapshot is not None: self.stack =stack_snapshot

    def stack_pop(self, stack=None):
        # pass by reference is a bit complicated in python
        stack_snapshot =None
        if stack is not None:
            stack_snapshot = self.stack
            self.stack = stack

        self.log(self.stack, "POP:")
        if stack_snapshot is not None:
            if self.stack is not None and len(self.stack) > 0:
                value =self.stack.pop()
                self.stack =stack_snapshot
                return value
            else:
                self.stack =stack_snapshot
                return None

        if self.stack is not None and len(self.stack) > 0:
            return self.stack.pop()
        else:
            return None
    
    def stack_top(self):
        # return the top element without popping it
        if self.stack is not None and len(self.stack) > 0:
            return self.stack[-1]
        else:
            return None
    """

    ##PARSE PROCESS################################################################
    # start the parsing process
    def parse_program(self):
        if not self.parse_statement():
            self.raise_error('Expected: statement')
        while self.peek_token() is not None:
            if not self.parse_statement():
                self.raise_error('Expected: statement')

        return True

    # TODO: inline parsing:^fd 100 rt 100 fd 100$
    def parse_statement(self, execute_builtin=True):
        if not self.parse_builtin_dictionary(execute_builtin) \
            and not self.parse_expression():
                self.raise_error('Unknown statement')

        # if next token is a command

        if self.peek_token() and self.peek_token().type != 'eol':
            breakpoint()
            if not self.parse_builtin_dictionary():
                self.raise_error("Expected: end of line")
        else:
            self.next_token()

        #### collapse the call stack for current line
        #breakpoint()
        self.call_stack

        return True

    def parse_expression(self):
        token =self.next_token()
        '''
        if token.type == 'identifier'
            and token.value not in self.subcommands:
            self.return_token(token)
            return False
        '''

        # TODO: track depth to introduce nested arrays
        if token.value == '[':
            list_ = []
            while True: 
                token =self.next_token()
                # if ] is encountered, break out of the loooop
                if token.value == ']': # end of array
                    break

                # variable inside a list
                if token.type == 'variable':
                    # dereference variable and check its existance
                    if self.base_env.get_env(token.value):
                        list_.append(self.base_env.get_env(token.value))
                        continue
                    else:
                        self.raise_error("Unknown variable name")
                else:
                    # if not var, just push value to stack
                    self.return_token(token)
                    self.parse_expression()
                    list_.append(self.stack.pop())

            self.stack.push(list_)

        # just a variable
        elif token.type == 'variable':
            if self.base_env.get_env(token.value):
                self.stack.push(self.base_env.get_env(token.value))
            else:
                self.raise_error("Unknown variable name")

        elif token.type == 'argv_begin':
            token = self.next_token()

            # check if next token is a procedure
            if token.type != 'identifier':
                self.raise_error("Expected: procedure call")

            procedure_name = token.value

            argc = 0
            while self.peek_token().type != 'argv_end':
                token = self.next_token()
                if token.type == 'string_literal':
                    self.stack.push(token.value)
                elif token.type == 'number_literal' or token.type == 'operator':
                    self.stack.push(token.value)
                else:
                    self.raise_error(f"Wrong type of argument: \"{token.value}\"")

                argc += 1
            #done
            self.next_token() # get the last )
            #NOTE: OLD self.builtins[procedure_name](argc)

            # execute the procedure
            arg_list = []
            for i in range(argc):
                arg_list.append(self.stack.pop())
            # fetch the procedure from the environment
            fref = self.base_env.get_env(procedure_name)
            if not fref:
                self.raise_error("Procedure does not exist")

            #fref.call(*arg_list)
            self.call_stack.push( (fref,arg_list))
        else:
            self.stack.push(token.value)

        return True

    def operator_expression(self):
        dispatch_operator = {
            '+': operator.add,
            '*': operator.mul,
            '/': operator.truediv
            #'-': operator.sub,
        }
        return True

    def parse_builtin_dictionary(self, execute=True):
        token =self.next_token()

        # if token.value is a procedure
        #if token.value not in self.builtin_dictionary:
        if token.value != self.base_env.get_env(token.value):
            self.return_token(token)
            self.log(token, "token was returned in parse_builtin:")
            return False

        if execute:
            # self.builtins[token.value](self)
            # fetch the procedure from the environment
            fref = self.base_env.get_env(token.value)
            if not fref:
                self.raise_error("Procedure does not exist")

            arg_list = []

            i = 0
            while True:
                value = self.stack.pop()
                if value is None: self.raise_error("Not enough arguments provided")
                else: arg_list.append(value)

                if i == fref.arg_count: break
                i+=1

            #fref.call(*arg_list)
            self.call_stack.push( (fref,arg_list) )

        return True

##PARSE PROCESS################################################################

##BUILTIN HANDLERS#############################################################
    def print_builtin(self, use_all_args=False, *args, **kwargs):
        print(*args, sep=" ", end="\n")
        return True

    def show_builtin(self, *args, **kwargs):
        print("[", sep="", end=" ")
        print(*args, end=" ")
        print("]", sep="", end="\n")

        '''
        while True:
            if value is None:
                print("]", sep="", end="\n")
                break

            if type(value) == list:
                for element in value:
                    print(element, sep=" ", end=" ")
            else:
                print(value, end=" ")
            #endif

        #done
        '''
        return True
    
    def repeat_builtin(self, *args, **kwargs):

        if self.peek_token().type != "number_literal":
            if not self.parse_expression():
                self.raise_error("Expected: number")

            iter_amount = self.stack.pop()
        else:
            iter_amount = self.next_token()

        # loop body
        if self.next_token().type != "list":
            self.raise_error("Expected: statement")
        statements = []
        while self.peek_token().type != "list":
            statements.append(self.next_token().value)

        breakpoint()
        return True

    def make_variable_builtin(self, *args, **kwargs):
        #token1 =self.next_token()
        #token0 =self.next_token()
        if not self.parse_expression():
            self.raise_error("Expected: expression")

        varname = self.stack.pop()
        if type(varname) != str:
            self.raise_error("Expected: name of the variable")

        if not self.parse_expression():
            self.raise_error("Expected: expression")

        varval = self.stack.pop()
        if type(varval) is None:
            self.raise_error("Unexpected error: null value")

        self.variable_dict[varname] = varval
        return True

    def sum_expressions_builtin(self):
        expr0, expr1 = None,None

        if not self.parse_expression():
            self.raise_error("Expected: expression")
        else:
            expr0 = self.stack.pop()

        if not self.parse_expression():
            self.raise_error("Expected: expression")
        else:
            expr1 = self.stack.pop()

        if type(expr0) != int or type(expr1) != int:
            self.raise_error("Can't sum different types")
        
        self.stack.push(expr0 + expr1)
        return True

##BUILTIN HANDLERS#############################################################
    def run(self):
        try:
            return self.parse_program()

        except ValueError as exc:
            print(str(exc))
            #print(f'{self.line_nr}:\t\033[0;31m{self.code[self.line_nr]}\033[0m')
            return False

def main():
    #if __name__ == "__main__":

    if len(argv) < 2:
        raise Exception("no input file")
        #TODO: stdin

    with open(argv[1], 'r') as fd:
        text =fd.read()

    lexer   =Logo(text,t)
    lexer.write_log =False
    lexer.run()

main()
