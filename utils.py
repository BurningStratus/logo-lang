
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

        if code_ln and self.write_log:
            print(f"Error raised on line: {code_ln}")
        raise ValueError(
            f'Error:\t{message} \
            \n{self.line_nr}:\t\033[0;31m{self.code[self.line_nr]}\033[0m')

