from procesador_directivas import ProcesadorDirectivas
from simbols.tabla_operaciones import TablaOperaciones
from generador_registros import GeneradorRegistros
from instruccion_processor import InstruccionProcessor

class ProcesadorLineas:
    def __init__(self):
        self.bloque_actual = 'DEFAULT'  # Estado inicial del bloque actual

    def procesar_linea(self, linea, contador_loc, tabla_simbolos, registros_modificacion, codigos_texto, codigos_objeto, tabla_bloques):
        """Procesa una línea de código y actualiza las tablas y registros correspondientes."""
        partes = linea.split()

        # Desglose de línea
        if len(partes) == 3:
            etiqueta, instruccion, operando = partes
        elif len(partes) == 2:
            etiqueta = None
            instruccion, operando = partes
        else:
            etiqueta = None
            instruccion = partes[0]
            operando = None

        # Inicia con el valor del CP para el bloque actual
        resultado = {'CP': f"{tabla_bloques[self.bloque_actual]['LOCCTR']:04X}"}
        codigo_objeto = ''

        # Si hay una etiqueta, agregarla a la tabla de símbolos
        if etiqueta:
            if etiqueta in tabla_simbolos:
                return {'Error': f"Error: Símbolo duplicado '{etiqueta}'"}
            if etiqueta == 'MAXLEN':
                tipo_simbolo = "Absoluto"
            else:
                tipo_simbolo = "Absoluto" if contador_loc < 0x1000 else "Relativo"
            tabla_simbolos[etiqueta] = (contador_loc, tipo_simbolo, self.bloque_actual)
            
            # Inicializar las etiquetas del bloque si no existe
            if 'etiquetas' not in tabla_bloques[self.bloque_actual]:
                tabla_bloques[self.bloque_actual]['etiquetas'] = []
            tabla_bloques[self.bloque_actual]['etiquetas'].append(etiqueta)

        # Procesar la directiva USE
        if instruccion == 'USE':
            if codigos_objeto:
                # Generar el registro de texto antes de procesar USE
                registro_texto = GeneradorRegistros.generar_registro_texto(contador_loc - len(codigos_objeto) // 2, ''.join(codigos_objeto))
                codigos_texto.append(registro_texto)
                codigos_objeto.clear()
            # Procesar la directiva USE y actualizar el contador de posición
            contador_loc = ProcesadorDirectivas.procesar_directiva_use(operando, contador_loc, tabla_bloques) + tabla_bloques[self.bloque_actual]['LOCCTR']
            resultado.update({'Instrucción': 'USE', 'Operando': operando or 'DEFAULT', 'Bloque': self.bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
            return resultado

        # Directivas RESB y RESW
        if instruccion == 'RESB':
            bytes_reservados = int(operando)
            if codigos_objeto:
                # Se debe generar el registro de texto antes de un espacio reservado
                registro_texto = GeneradorRegistros.generar_registro_texto(contador_loc, ''.join(codigos_objeto))
                codigos_texto.append(registro_texto)
                codigos_objeto.clear()
            contador_loc += bytes_reservados
            resultado.update({'Instrucción': 'RESB', 'Operando': operando, 'Bloque': self.bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
            return resultado

        if instruccion == 'RESW':
            palabras_reservadas = int(operando)
            if codigos_objeto:
                # Se debe generar el registro de texto antes de un espacio reservado
                registro_texto = GeneradorRegistros.generar_registro_texto(contador_loc, ''.join(codigos_objeto))
                codigos_texto.append(registro_texto)
                codigos_objeto.clear()
            contador_loc += palabras_reservadas * 3  # Cada palabra es de 3 bytes
            resultado.update({'Instrucción': 'RESW', 'Operando': operando, 'Bloque': self.bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
            return resultado

        if instruccion in TablaOperaciones.TABOP:
            codigo_operacion, formato = TablaOperaciones.TABOP[instruccion]

            if codigo_operacion is not None:  # Instrucción válida
                if not InstruccionProcessor.validar_sintaxis(instruccion, operando, formato):
                    return {'Error': "Error de sintaxis en los operandos"}
                codigo_objeto, tipo_simbolo = InstruccionProcessor.ensamblar_instruccion(instruccion, operando, tabla_simbolos, contador_loc, registros_modificacion)

            else:  # Directivas como BYTE, WORD
                if instruccion in ['BYTE', 'WORD']:  # Verifica si la instrucción es BYTE o WORD
                    codigo_objeto, tipo_simbolo = InstruccionProcessor.ensamblar_instruccion(instruccion, operando, tabla_simbolos, contador_loc, registros_modificacion)
                else:
                    codigo_objeto = "Directiva"
        else:
            # Manejar el caso donde la instrucción no está en TABOP
            return {'Error': f"Error: La instrucción no existe"}
        
        # Manejo de registros de texto
        if codigo_objeto != "Directiva" and codigo_objeto:
            codigos_objeto.append(codigo_objeto)

        if instruccion in ['EQU', 'USE', 'RESB', 'RESW'] or len(''.join(codigos_objeto)) >= 60:
            if codigos_objeto:
                direccion_inicio_programa = tabla_bloques[self.bloque_actual]['INICIO']
                registro_texto = GeneradorRegistros.generar_registro_texto(tabla_bloques[self.bloque_actual]['LOCCTR'] + direccion_inicio_programa - len(codigos_objeto) // 2, ''.join(codigos_objeto))
                codigos_texto.append(registro_texto)
                codigos_objeto.clear()
                
        resultado.update({
            'Etiqueta': etiqueta if etiqueta else '',
            'Instrucción': instruccion,
            'Operando': operando if operando else '',
            'Código Objeto': codigo_objeto if codigo_objeto != "Directiva" else '',
            'Bloque': self.bloque_actual
        })

        return resultado
