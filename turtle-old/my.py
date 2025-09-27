#!/sbin/python
import operator
import re as regex
import turtle as t

#https://www.calormen.com/jslogo/language.html
class Logo:
    def __init__(self, text, t=None):
        self.t  =t.Turtle()
            
        self.code       =self.preprocessor(text)
        self.line_nr    =0
        self.token_feed =self.tokens()
        self.returned_token =None
        self.stack =[]

        self.dispatch = {
            '+': operator.add,
            #'-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }
        self.dispatch_movefunc = {
            'forward':  self.t.forward,
            'backward': self.t.backward,
            'right':    self.t.right,
            'left':     self.t.left,
            'setx':     self.t.setx,
            'sety':     self.t.sety,
        }
        self.movlist = ['forward','backward','right','left','setx','sety']
    
    # strip of whitespace
    def preprocessor(self, text):
        text_f =regex.sub(r'#.*$', '', text, flags=regex.MULTILINE)

        text_f =regex.sub(r'^\s*$\n?', '', text_f, flags=regex.MULTILINE)
        return text_f


    def pushs(self, arg):
        self.stack.append(arg)
        #print("PUSH:", self.stack)

    def pops(self):
        #print("POP:", self.stack)
        return self.stack.pop()

    def raise_error(self, message):
        raise ValueError(f'{self.line_nr}: {message}')

    def tokens(self):
        for line in self.code.strip().split('\n'):
            self.line_nr += 1
            for token in line.strip().split(' '):
                if token == 'show':
                    yield (token,)
                if token in self.dispatch_movefunc:
                    yield (token,)
                elif len(token) == 1 and token in "+-*/()":
                    yield ('op',token)
                elif token.isnumeric():
                    yield ('number', int(token))
                elif token.isalpha():
                    yield ('string', str(token))
                elif not token:
                    continue
                else:
                    self.raise_error(f'Syntax Error: Invalid token {token}')
            yield ('\n',)

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

    # start the parsing process
    def parse_program(self):
        if not self.parse_statement():
            self.raise_error('Expected: statement')

        token = self.ntok()
        while token is not None:
            self.rtok(token)
            if not self.parse_statement():
               self.raise_error('Expected: statement')
            token = self.ntok()
        return True

    def parse_statement(self):
        if not self.parse_print_statement() \
            and not self.parse_expr_statement() \
            and not self.parse_move_statement():
            self.raise_error('Unknown statement')
        token = self.ntok()
        if token[0] != '\n':
            self.raise_error('Expected: end of line')
        return True

    def parse_print_statement(self):
        token =self.ntok()
        if token[0] != 'show':
            self.rtok(token)
            return False

        if not self.parse_expression() and not self.parse_expr_statement():
            self.raise_error('Expected: expression')

        print(self.pops())
        return True

    def parse_move_statement(self):
        token =self.ntok()
        if token[0] not in self.dispatch_movefunc:
            self.rtok(token)
            return False

        if not self.parse_expression() and not self.parse_expr_statement():
            self.raise_error('Expected: expression')

        self.dispatch_movefunc[token[0]](self.pops())
        return True

    def parse_expression(self):
        token = self.ntok()
        if token[0] != 'number':
            self.rtok(token)
            return False
        
        self.pushs(token[1])
        return True

    def parse_expr_statement(self):
        token =self.ntok()
        if token != ('op','('):
            self.rtok(token)
            return False

        while token[1] !=')' :
            self.pushs(token[1])
            token =self.ntok()

        self.pushs(token[1])

        calcvalue =self.math_expr()
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
                
            tmpstack.append(self.dispatch[ths](prv, nxt))

        #print(tmpstack)
        # end of expr, remove the (
        cval =self.pops()
        self.pushs(tmpstack.pop())

        return True

    def run(self):
        try:
            return self.parse_program()
        except ValueError as exc:
            print(str(exc))
            return False

if __name__ == "__main__":
    with open('sample.cfg', 'r') as fd:
        text =fd.read()

    lexer   =Logo(text,t)
    lexer.run()

    # TODO ARG VECTOR

