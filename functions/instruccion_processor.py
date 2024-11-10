from evaluador_expresion import EvaluadorExpresion
from simbols.tabla_operaciones import TABOP
from generador_registros import GeneradorRegistros

class InstruccionProcessor:
    def __init__(self, tabla_simbolos, tabla_bloques):
        self.tabla_simbolos = tabla_simbolos
        self.tabla_bloques = tabla_bloques
        self.bloque_actual = 'DEFAULT'  # Inicializar el bloque actual si es necesario

    def validar_sintaxis(self, instruccion, operando, formato):
        """Valida la cantidad de operandos según el formato de la instrucción"""
        if instruccion == 'BYTE':
            if operando.startswith("C'") and operando.endswith("'"):
                return True
            elif operando.startswith("X'") and operando.endswith("'"):
                # Validar que el valor hexadecimal tenga una longitud válida (debe ser par)
                valor_hex = operando[2:-1]
                return len(valor_hex) % 2 == 0
            return False

        if formato == 1:
            return operando is None
        elif formato == 2:
            operandos = operando.split(',') if operando else []
            return len(operandos) == 1 or len(operandos) == 2
        elif formato in [3, 4]:  # Instrucciones de formato 3 o 4
            return operando is not None
        return False

    def ensamblar_instruccion(self, instruccion, operando, contador_loc, registros_modificacion):
        """Ensambla la instrucción y devuelve el código objeto y tipo de dirección"""
        global bloque_actual  # Para acceder al bloque actual
        
        # Verificar si la instrucción está en TABOP
        if instruccion not in TABOP:
            return '', "Error: Instrucción no soportada"

        # Instrucción BYTE
        if instruccion == 'BYTE':
            if operando.startswith("C'") and operando.endswith("'"):
                caracteres = operando[2:-1]  # Eliminar C' y '
                codigo_objeto = ''.join(f"{ord(c):02X}" for c in caracteres)
                return codigo_objeto, "Absoluto"
            elif operando.startswith("X'") and operando.endswith("'"):
                valor_hex = operando[2:-1]  # Eliminar X' y '
                codigo_objeto = valor_hex.upper()
                return codigo_objeto, "Absoluto"
            else:
                return '', "Error: Formato de operando inválido para BYTE"

        # Instrucción WORD
        elif instruccion == 'WORD':
            if any(op in operando for op in '+-*/'):
                valor, tipo_direccion = EvaluadorExpresion.evaluar_expresion(operando)
                if tipo_direccion == "Error":
                    return '', "Error: Evaluación de expresión fallida"
            else:
                valor = int(operando)
                tipo_direccion = "Absoluto"

            return f"{valor:06X}", tipo_direccion

        # Para instrucciones de formato 2
        codigo_operacion, formato = TABOP[instruccion]
        direccion = 0
        
        if formato == 2:
            # Manejar operando con prefijos @ y #
            if operando.startswith('#'):
                n, i = 0, 0  # Inmediato
                operando = operando[1:]  # Eliminar el prefijo
            elif operando.startswith('@'):
                n, i = 1, 0  # Indirecto
                operando = operando[1:]  # Eliminar el prefijo
            else:
                n, i = 1, 1  # Directo

            # Obtener el código de operación
            codigo_objeto = (codigo_operacion << 12)

            # Aquí podrías agregar más lógica para procesar el operando si es necesario
            return f"{codigo_objeto:04X}", "Absoluto"  # Retornar como absoluto para consistencia
        
        elif formato == 3 or formato == 4:
            # Evaluar si el operando es una expresión
            if operando and any(op in operando for op in '+-*/'):
                direccion, tipo_direccion = EvaluadorExpresion.evaluar_expresion(operando)
                if tipo_direccion == "Error":
                    return '', "Error: Evaluación de expresión fallida"
            else:
                # Buscar el símbolo en la tabla
                direccion, tipo_direccion, bloque = self.tabla_simbolos.get(operando, (0xFFFF, 'Error', None))

                if tipo_direccion == "Error":
                    # Simbolo no encontrado, usar dirección por defecto
                    direccion = 0xFFFF
                    bloque = None

            # Ajustar la dirección considerando el inicio del programa
            direccion_inicio_programa = self.tabla_bloques[bloque]['LOCCTR'] if bloque is not None else 0
            direccion += direccion_inicio_programa

            # Configurar los bits n/i/x/b/p/e y armar el código objeto
            n, i, x, b, p, e = 1, 1, 0, 0, 0, 0  # Valores por defecto

            # Asignar valores a n e i dependiendo del prefijo del operando
            if operando.startswith('#'):
                n, i = 0, 0  # Inmediato
            elif operando.startswith('@'):
                n, i = 1, 0  # Indirecto

            if formato == 3:
                desplazamiento = direccion - (contador_loc + 3)
                if -2048 <= desplazamiento <= 2047:
                    p = 1  # Uso de desplazamiento relativo
                else:
                    b = 1  # Uso de la base (en caso de ser necesario)

            elif formato == 4:
                e = 1  # Formato extendido

            # Generar el registro de modificación
            registros_modificacion.append(GeneradorRegistros.generar_registro_modificacion(contador_loc + 1))

            # Armar el código objeto
            codigo_objeto = (codigo_operacion << 16) | (n << 17) | (i << 16) | (x << 15) | (b << 14) | (p << 13) | (e << 12) | (direccion & 0xFFF)

            return f"{codigo_objeto:06X}", "Absoluto"  # Devolver como absoluto para mantener consistencia

        return '', "Error: Instrucción no soportada"
