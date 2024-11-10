from evaluador_expresion import EvaluadorExpresion

class ProcesadorDirectivas:
    def __init__(self):
        self.bloque_actual = 'DEFAULT'  # Estado inicial del bloque actual

    def procesar_directiva_equ(self, etiqueta, operando, tabla_simbolos, contador_loc):
        """Evalúa la expresión de EQU y actualiza la tabla de símbolos."""
        valor, tipo = EvaluadorExpresion.evaluar(operando, tabla_simbolos)
        if valor is not None:
            tabla_simbolos[etiqueta] = (valor, tipo)
        else:
            return {'Error': tipo}  # Retorna el error si la expresión no es válida
        return None

    def procesar_directiva_use(self, operando, contador_loc, tabla_bloques):
        """Cambia al bloque especificado o al bloque DEFAULT si no se proporciona un operando."""
        # Si hay un bloque actual, guardar el estado del contador LOCCTR antes de cambiar
        if self.bloque_actual:
            # Actualizar el LOCCTR del bloque actual antes de cambiar
            tabla_bloques[self.bloque_actual]['LOCCTR'] = contador_loc

        # Cambiar al bloque especificado o al bloque DEFAULT si no se proporciona un operando
        if operando:  # Si hay un bloque específico
            if operando not in tabla_bloques:
                # Crear nuevo bloque si no existe
                tabla_bloques[operando] = {
                    'LOCCTR': 0x0000,  # Inicializar LOCCTR del nuevo bloque en 0
                    'TAMANO': 0,       # Tamaño que será calculado al final
                    'NUMERO': len(tabla_bloques),
                    'INICIO': contador_loc  # Guardar dirección de inicio
                }
            self.bloque_actual = operando  # Cambiar al bloque específico
        else:
            # Volver al bloque por omisión si no hay operando
            self.bloque_actual = 'DEFAULT'

            # Asegurarse de que el bloque DEFAULT exista
            if self.bloque_actual not in tabla_bloques:
                tabla_bloques[self.bloque_actual] = {
                    'LOCCTR': 0x0000,
                    'TAMANO': 0,
                    'NUMERO': len(tabla_bloques),
                    'INICIO': contador_loc  # Guardar dirección de inicio
                }

        # Actualizar el contador LOCCTR del bloque actual
        tabla_bloques[self.bloque_actual]['LOCCTR'] = contador_loc

        # Retornar el LOCCTR actualizado del bloque actual
        return tabla_bloques[self.bloque_actual]['LOCCTR']
