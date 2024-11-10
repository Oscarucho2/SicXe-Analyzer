class TablaOperaciones:
    def __init__(self):
        # Definimos la tabla de operaciones en un diccionario
        self.tabla = {
            'LDA': (0x00, 3), 'LDX': (0x04, 3), 'LDL': (0x08, 3),
            'STA': (0x0C, 3), 'STX': (0x10, 3), 'STL': (0x14, 3),
            'ADD': (0x18, 3), 'SUB': (0x1C, 3), 'MUL': (0x20, 3),
            'DIV': (0x24, 3), 'COMP': (0x28, 3), 'TIX': (0x2C, 3),
            'JEQ': (0x30, 3), 'JGT': (0x34, 3), 'JLT': (0x38, 3),
            'J': (0x3C, 3), 'JSUB': (0x48, 3), 'RSUB': (0x4C, 3),
            'LDCH': (0x50, 3), 'STCH': (0x54, 3), 'LDT': (0x0A, 3),

            '+LDA': (0x00, 4), '+LDX': (0x04, 4), '+LDL': (0x08, 4),
            '+STA': (0x0C, 4), '+STX': (0x10, 4), '+STL': (0x14, 4),
            '+ADD': (0x18, 4), '+SUB': (0x1C, 4), '+MUL': (0x20, 4),
            '+DIV': (0x24, 4), '+COMP': (0x28, 4), '+TIX': (0x2C, 4),
            '+JEQ': (0x30, 4), '+JGT': (0x34, 4), '+JLT': (0x38, 4),
            '+J': (0x3C, 4), '+JSUB': (0x48, 4), '+RSUB': (0x4C, 4),
            '+LDCH': (0x50, 4), '+STCH': (0x54, 4), '+LDT': (0x0A, 3),

            'WORD': (None, 'directiva'), 'BYTE': (None, 'directiva'),
            'START': (None, 'directiva'), 'END': (None, 'directiva'),
            'RESW': (None, 'directiva'), 'RESB': (None, 'directiva'),
            'EQU': (None, 'directiva'), 'USE': (None, 'directiva'),

            # Instrucciones de formato 1
            'FIX': (0xC4, 1), 'FLOAT': (0xC0, 1), 'NORM': (0xC8, 1),
            'SIO': (0xF0, 1), 'HIO': (0xF4, 1), 'TIO': (0xF8, 1),

            # Instrucciones de formato 2
            'ADDR': (0x90, 2), 'SUBR': (0x94, 2), 'MULR': (0x98, 2),
            'DIVR': (0x9C, 2), 'COMPR': (0xA0, 2), 'TIXR': (0xB8, 2),
            'CLEAR': (0xB4, 2),
        }

    def obtener_codigo_operacion(self, instruccion):
        """Devuelve el código de operación de la instrucción dada."""
        if instruccion in self.tabla:
            return self.tabla[instruccion][0]
        return None

    def obtener_formato(self, instruccion):
        """Devuelve el formato de la instrucción dada (1, 2, 3, 4 o 'directiva')."""
        if instruccion in self.tabla:
            return self.tabla[instruccion][1]
        return None

    def es_instruccion_valida(self, instruccion):
        """Verifica si una instrucción está en la tabla."""
        return instruccion in self.tabla
