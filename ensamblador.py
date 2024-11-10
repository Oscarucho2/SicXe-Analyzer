
import re
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

class EditorConNumerosLinea(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)

        # Crear el área de números de línea
        self.line_numbers = tk.Text(self, width=4, padx=5, takefocus=0, border=0,
                                    background='lightgrey', state='disabled', wrap='none')
        self.text_widget = ScrolledText(self, wrap=tk.NONE)
        
        # Colocar ambos widgets en la interfaz
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.text_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Configurar eventos para actualizar números de línea
        self.text_widget.bind("<KeyRelease>", self.actualizar_numeros_linea)
        self.text_widget.bind("<MouseWheel>", self.actualizar_numeros_linea)

    def actualizar_numeros_linea(self, event=None):
        # Activar y limpiar el widget de números de línea para actualizarlo
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", tk.END)

        # Obtener el número total de líneas en el text widget
        total_lineas = int(self.text_widget.index('end').split('.')[0]) - 1

        # Generar los números de línea
        lineas = "\n".join(str(i) for i in range(1, total_lineas + 1))
        self.line_numbers.insert("1.0", lineas)

        # Desactivar el widget de números de línea para evitar edición
        self.line_numbers.config(state="disabled")
        
# Tablas de operaciones y sus formatos (Ejemplo)
TABOP = {
    'LDA': (0x00, 3), 'LDX': (0x04, 3), 'LDL': (0x08, 3),
    'STA': (0x0C, 3), 'STX': (0x10, 3), 'STL': (0x14, 3),
    'ADD': (0x18, 3), 'SUB': (0x1C, 3), 'MUL': (0x20, 3),
    'DIV': (0x24, 3), 'COMP': (0x28, 3), 'TIX': (0x2C, 3),
    'JEQ': (0x30, 3), 'JGT': (0x34, 3), 'JLT': (0x38, 3),
    'J': (0x3C, 3), 'JSUB': (0x48, 3), 'RSUB': (0x4C, 3),
    'LDCH': (0x50, 3), 'STCH': (0x54, 3),'LDT': (0x0A,3),
    
    '+LDA': (0x00, 4), '+LDX': (0x04, 4), '+LDL': (0x08, 4),
    '+STA': (0x0C, 4), '+STX': (0x10, 4), '+STL': (0x14, 4),
    '+ADD': (0x18, 4), '+SUB': (0x1C, 4), '+MUL': (0x20, 4),
    '+DIV': (0x24, 4), '+COMP': (0x28, 4), '+TIX': (0x2C, 4),
    '+JEQ': (0x30, 4), '+JGT': (0x34, 4), '+JLT': (0x38, 4),
    '+J': (0x3C, 4), '+JSUB': (0x48, 4), '+RSUB': (0x4C, 4),
    '+LDCH': (0x50, 4), '+STCH': (0x54, 4),'+LDT': (0x0A,4),

    'WORD': (None, 'directiva'), 'BYTE': (None, 'directiva'),
    'START': (None, 'directiva'), 'END': (None, 'directiva'),
    'RESW': (None, 'directiva'), 'RESB': (None, 'directiva'),
    'EQU': (None, 'directiva'), 'USE': (None, 'directiva'),
    'ORG': (None, 'directiva'),

    # Instrucciones de formato 1
    'FIX': (0xC4, 1), 'FLOAT': (0xC0, 1), 'NORM': (0xC8, 1),
    'SIO': (0xF0, 1), 'HIO': (0xF4, 1), 'TIO': (0xF8, 1),

    # Instrucciones de formato 2
    'ADDR': (0x90, 2), 'SUBR': (0x94, 2), 'MULR': (0x98, 2),
    'DIVR': (0x9C, 2), 'COMPR': (0xA0, 2), 'TIXR': (0xB8, 2),
    'CLEAR': (0xB4, 2), 'SHIFTL': (0xA8, 2), 
}

tabla_bloques = {
    'DEFAULT': {'LOCCTR': 0x0000, 'TAMANO': 0, 'NUMERO': 0}  # Bloque por omisión
}
bloque_actual = 'DEFAULT'  # Bloque actual (inicialmente por defecto)
contador_loc_bloques = {bloque_actual: 0x0000}  # Contador LOCCTR por bloque

# Modificar la tabla de símbolos para incluir el bloque
tabla_simbolos = {}  # Simbolo: (Direccion, Tipo, Bloque)
nombre_programa_global = None

def evaluar_expresion(expresion, tabla_simbolos):
    # Tokenizamos la expresión, separando números, operadores y paréntesis
    tokens = re.findall(r'[A-Za-z_]\w*|[+\-*/()]|\d+', expresion)

    pila_valores = []
    pila_operadores = []
    pila_tipos = []  # Almacenar los tipos de los términos (Absoluto o Relativo)

    def aplicar_operador(operador, b, a):
        """Aplica un operador (+, -, *, /) entre dos valores a y b."""
        if operador == '+':
            return a + b
        elif operador == '-':
            return a - b
        elif operador == '*':
            return a * b
        elif operador == '/':
            if b == 0:
                raise ZeroDivisionError("División por cero")
            return a // b
        else:
            raise ValueError(f"Operador no reconocido: {operador}")

    def procesar_pila():
        """Procesa la pila de operadores y valores hasta resolver la expresión."""
        while pila_operadores:
            operador = pila_operadores.pop()
            b = pila_valores.pop()
            a = pila_valores.pop()
            tipo_b = pila_tipos.pop()
            tipo_a = pila_tipos.pop()

            # Verificamos que no se usen términos relativos en multiplicación o división
            if operador in '* /' and (tipo_b == 'R' or tipo_a == 'R'):
                raise ValueError(f"Error: No se permiten términos relativos en operaciones de multiplicación o división: {expresion}")

            # Si ambos términos son relativos y los operadores están balanceados, marcamos la expresión como absoluta
            if tipo_a == tipo_b == 'R' and (operador == '+' or operador == '-'):
                tipo_resultado = 'R'
            else:
                tipo_resultado = 'A'
            
            pila_valores.append(aplicar_operador(operador, b, a))
            pila_tipos.append(tipo_resultado)

    # Procesamos cada token
    for token in tokens:
        if token.isdigit():  # Si el token es un número
            pila_valores.append(int(token))
            pila_tipos.append('A')  # Es un término absoluto
        elif re.match(r'[A-Za-z_]\w*', token):  # Si es una etiqueta o símbolo
            if token not in tabla_simbolos:
                raise ValueError(f"Símbolo no reconocido: {token}")
            
            # Obtenemos el valor y tipo de dirección del símbolo, asegurándonos de solo desempacar dos elementos
            entrada_simbolo = tabla_simbolos[token]
            valor = entrada_simbolo[0]  # Obtener solo el valor
            tipo = entrada_simbolo[1]   # Obtener el tipo de dirección

            pila_valores.append(valor)
            pila_tipos.append(tipo)  # Guardamos si el símbolo es absoluto ('A') o relativo ('R')
        elif token == '(':  # Abre paréntesis
            pila_operadores.append(token)
        elif token == ')':  # Cierra paréntesis
            while pila_operadores and pila_operadores[-1] != '(':
                operador = pila_operadores.pop()
                b = pila_valores.pop()
                a = pila_valores.pop()
                tipo_b = pila_tipos.pop()
                tipo_a = pila_tipos.pop()
                pila_valores.append(aplicar_operador(operador, b, a))
                pila_tipos.append('A')  # Los resultados intermedios serán absolutos (a menos que se indique lo contrario)
            pila_operadores.pop()  # Quitamos el '('
        elif token in '+-*/':  # Si es un operador
            while (pila_operadores and pila_operadores[-1] in '+-*/' and
                pila_operadores[-1] != '('):
                operador = pila_operadores.pop()
                b = pila_valores.pop()
                a = pila_valores.pop()
                tipo_b = pila_tipos.pop()
                tipo_a = pila_tipos.pop()
                pila_valores.append(aplicar_operador(operador, b, a))
                pila_tipos.append('A')  # Los resultados intermedios serán absolutos (a menos que se indique lo contrario)
            pila_operadores.append(token)
        else:
            raise ValueError(f"Símbolo o operador no reconocido: {token}")

    # Procesamos los operadores restantes
    procesar_pila()

    if len(pila_valores) != 1:
        raise ValueError("Error en la evaluación de la expresión")

    valor_final = pila_valores[0]
    tipo_direccion = 'relativo' if 'R' in pila_tipos else 'absoluto'  # Si hay un tipo relativo, la expresión es relativa

    return valor_final, tipo_direccion


def generar_registro_encabezado(nombre_programa, inicio, longitud):
    return f"H{nombre_programa[:6].ljust(6)}{inicio:06X}{longitud:06X}"

def generar_registro_texto(inicio, codigos_objeto):
    longitud = len(codigos_objeto) // 2
    return f"T{inicio:06X}{longitud:02X}{codigos_objeto}"

def generar_registro_modificacion(direccion):
    return f"M{direccion:06X}05" + "+" + nombre_programa_global  # Longitud 5 bytes para formato 4

def generar_registro_fin(inicio):
    return f"E{inicio:06X}"

def evaluar_expresion_equ(expresion, tabla_simbolos, contador_loc):
    """
    Evalúa una expresión usando los símbolos definidos en la tabla de símbolos.
    """
    if expresion == '*':
        return contador_loc, "Absoluto"  # Devolver el valor del contador de program
    # Reemplazar símbolos en la expresión
    for simbolo, (valor, tipo, _) in tabla_simbolos.items():
        expresion = re.sub(rf'\b{simbolo}\b', str(valor), expresion)

    # Manejo de notaciones hexadecimales
    expresion = re.sub(r'(\d+)H', lambda x: str(int(x.group(1), 16)), expresion)

    # Reemplazar la división para forzar enteros (redondeo hacia abajo)
    expresion = re.sub(r'(\d+)\s*/\s*(\d+)', lambda x: f"{int(int(x.group(1)) // int(x.group(2)))}", expresion)

    try:
        resultado = eval(expresion)
        # Asegurarse de que el resultado sea un entero
        resultado = int(resultado)

        # Determinar si el resultado es absoluto o relativo
        if any(simbolo in expresion for simbolo, (_, tipo, _) in tabla_simbolos.items() if tipo == "Relativo"):
            tipo_resultado = "Relativo"
        else:
            tipo_resultado = "Absoluto"
        return resultado, tipo_resultado
    except (SyntaxError, NameError):
        raise ValueError("Error: La expresión contiene símbolos no definidos o tiene un formato incorrecto.")
    except ZeroDivisionError:
        raise ValueError("Error: División por cero en la expresión.")

def procesar_directiva_use(operando, contador_loc, tabla_bloques):
    global bloque_actual
    
    # Si hay un bloque actual, guardar el estado del contador LOCCTR antes de cambiar
    if bloque_actual:
        # Actualizar el LOCCTR del bloque actual antes de cambiar
        tabla_bloques[bloque_actual]['LOCCTR'] = contador_loc

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
        bloque_actual = operando  # Cambiar al bloque específico
    else:
        # Volver al bloque por omisión si no hay operando
        bloque_actual = 'DEFAULT'

        # Asegurarse de que el bloque DEFAULT exista
        if bloque_actual not in tabla_bloques:
            tabla_bloques[bloque_actual] = {
                'LOCCTR': 0x0000,
                'TAMANO': 0,
                'NUMERO': len(tabla_bloques),
                'INICIO': contador_loc  # Guardar dirección de inicio
            }

    # Actualizar el contador LOCCTR del bloque actual
    tabla_bloques[bloque_actual]['LOCCTR'] = contador_loc

    # Retornar el LOCCTR actualizado del bloque actual
    return tabla_bloques[bloque_actual]['LOCCTR']


def procesar_linea(linea, contador_loc, tabla_simbolos, registros_modificacion, codigos_texto, codigos_objeto, tabla_bloques):
    global bloque_actual

    partes = linea.split()
    print(linea)
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
    resultado = {'CP': f"{tabla_bloques[bloque_actual]['LOCCTR']:04X}"}
    codigo_objeto = ''

    # Si hay una etiqueta, agregarla a la tabla de símbolos
    if etiqueta:
        if etiqueta in tabla_simbolos:
            return {'Error': f"Error: Símbolo duplicado '{etiqueta}'"}
        if etiqueta == 'MAXLEN':
            tipo_simbolo = "Absoluto"
        else:
            tipo_simbolo = "Relativo" if contador_loc < 0x1000 else "Absoluto"
        tabla_simbolos[etiqueta] = (contador_loc, tipo_simbolo, bloque_actual)
        
        # Inicializar las etiquetas del bloque si no existe
        if 'etiquetas' not in tabla_bloques[bloque_actual]:
            tabla_bloques[bloque_actual]['etiquetas'] = []
        tabla_bloques[bloque_actual]['etiquetas'].append(etiqueta)

  # Directiva EQU
    if instruccion == 'EQU':
        try:
            # Evaluar la expresión del operando
            valor, tipo = evaluar_expresion_equ(operando, tabla_simbolos, contador_loc)
            # Añadir el símbolo con su valor y tipo a la tabla de símbolos
            tabla_simbolos[etiqueta] = (valor, tipo, bloque_actual)
            resultado.update({'Instrucción': 'EQU', 'Operando': operando, 'Bloque': bloque_actual, 'Etiqueta': etiqueta, 'Código Objeto': ''})
            return resultado
        except ValueError as e:
            return {'Error': str(e)}

    # Directiva ORG
    if instruccion == 'ORG':
        try:
            if operando.endswith('H'):  # Si tiene una H, interpretarlo como hexadecimal
                nuevo_cp = int(operando[:-1], 16)
            else:  # Si no tiene H, interpretarlo como decimal y convertirlo
                nuevo_cp = int(operando)
            contador_loc = nuevo_cp  # Cambiar el CP directamente
            tabla_bloques[bloque_actual]['LOCCTR'] = contador_loc  # Actualizar LOCCTR en el bloque actual
            resultado.update({'Instrucción': 'ORG', 'Operando': operando, 'Bloque': bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
            return resultado
        except ValueError:
            return {'Error': "Error: Operando inválido para ORG"}

    # Directiva USE
    if instruccion == 'USE':
        if codigos_objeto:
            # Generar el registro de texto antes de procesar USE
            registro_texto = generar_registro_texto(contador_loc - len(codigos_objeto) // 2, ''.join(codigos_objeto))
            codigos_texto.append(registro_texto)
            codigos_objeto.clear()
        # Procesar la directiva USE y actualizar el contador de posición
        contador_loc = procesar_directiva_use(operando, contador_loc, tabla_bloques) + tabla_bloques[bloque_actual]['LOCCTR']
        resultado.update({'Instrucción': 'USE', 'Operando': operando or 'DEFAULT', 'Bloque': bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
        return resultado

    # Directivas RESB y RESW
    if instruccion == 'RESB':
        bytes_reservados = int(operando)
        if codigos_objeto:
            # Se debe generar el registro de texto antes de un espacio reservado
            registro_texto = generar_registro_texto(contador_loc, ''.join(codigos_objeto))
            codigos_texto.append(registro_texto)
            codigos_objeto.clear()
        contador_loc += bytes_reservados
        resultado.update({'Instrucción': 'RESB', 'Operando': operando, 'Bloque': bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
        return resultado

    if instruccion == 'RESW':
        palabras_reservadas = int(operando)
        if codigos_objeto:
            # Se debe generar el registro de texto antes de un espacio reservado
            registro_texto = generar_registro_texto(contador_loc, ''.join(codigos_objeto))
            codigos_texto.append(registro_texto)
            codigos_objeto.clear()
        contador_loc += palabras_reservadas * 3  # Cada palabra es de 3 bytes
        resultado.update({'Instrucción': 'RESW', 'Operando': operando, 'Bloque': bloque_actual, 'Etiqueta': etiqueta or '', 'Código Objeto': ''})
        return resultado

    if instruccion in TABOP:
        codigo_operacion, formato = TABOP[instruccion]

        if codigo_operacion is not None:  # Instrucción válida
            if not validar_sintaxis(instruccion, operando, formato):
                return {'Error': "Error de sintaxis en los operandos"}
            codigo_objeto, tipo_simbolo = ensamblar_instruccion(instruccion, operando, tabla_simbolos, contador_loc, registros_modificacion)

        else:  # Directivas como BYTE, WORD
            if instruccion in ['BYTE', 'WORD']:  # Verifica si la instrucción es BYTE o WORD
                codigo_objeto, tipo_simbolo = ensamblar_instruccion(instruccion, operando, tabla_simbolos, contador_loc, registros_modificacion)
            else:
                codigo_objeto = "Directiva"
    else:
        # Manejar el caso donde la instrucción no está en TABOP
        return {'Error': f"Error: La instrucción no existe"}
    
    # Manejo de registros de texto
    if codigo_objeto != "Directiva" and codigo_objeto:
        codigos_objeto.append(codigo_objeto)

    if instruccion in ['EQU', 'USE', 'RESB', 'RESW', 'ORG'] or len(''.join(codigos_objeto)) >= 60:
        if codigos_objeto:
            direccion_inicio_programa = tabla_bloques[bloque_actual]['inicio']
            registro_texto = generar_registro_texto(tabla_bloques[bloque_actual]['LOCCTR'] + direccion_inicio_programa - len(codigos_objeto) // 2, ''.join(codigos_objeto))
            codigos_texto.append(registro_texto)
            codigos_objeto.clear()
            
    resultado.update({
        'Etiqueta': etiqueta if etiqueta else '',
        'Instrucción': instruccion,
        'Operando': operando if operando else '',
        'Código Objeto': codigo_objeto if codigo_objeto != "Directiva" else '',
        'Bloque': bloque_actual
    })

    return resultado


def validar_sintaxis(instruccion, operando, formato):
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

def ensamblar_instruccion(instruccion, operando, tabla_simbolos, contador_loc, registros_modificacion):
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
            valor, tipo_direccion = evaluar_expresion_equ(operando, tabla_simbolos, contador_loc)
            if tipo_direccion == "Error":
                return '', "Error: Evaluación de expresión fallida"
        else:
            valor = int(operando)
            tipo_direccion = "Absoluto"

        return f"{valor:06X}", tipo_direccion

    # Para instrucciones de formato 2
    codigo_operacion, formato = TABOP[instruccion]
    
    # Manejo de la bandera "X"
    usar_extendido = 'X' in operando.split(',')
    operando = operando.split(',')[0].strip()  # Eliminar cualquier bandera que siga a la coma

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

        return f"{codigo_objeto:04X}", "Absoluto"  # Retornar como absoluto para consistencia
    
    elif formato == 3 or formato == 4:
        # Evaluar si el operando es una expresión
        if operando and any(op in operando for op in '+-*/'):
            try:
                direccion, tipo_direccion = evaluar_expresion_equ(operando, tabla_simbolos, contador_loc)
                if tipo_direccion == "Error":
                    return '', "Error: Evaluación de expresión fallida"
            except ValueError:
                return '', "Error: Evaluación de expresión fallida"
        else:
            # Buscar el símbolo en la tabla
            direccion, tipo_direccion, bloque = tabla_simbolos.get(operando, (0xFFFF, 'Error', None))

            if tipo_direccion == "Error":
                # Simbolo no encontrado, usar dirección por defecto
                direccion = 0xFFFF
                bloque = None

        # Ajustar la dirección considerando el inicio del programa
        direccion_inicio_programa = tabla_bloques[bloque]['LOCCTR'] if bloque is not None else 0
        direccion += direccion_inicio_programa

        # Configurar los bits n/i/x/b/p/e y armar el código objeto
        n, i, x, b, p, e = 1, 1, 0, 0, 0, 0  # Valores por defecto

        # Asignar valores a n e i dependiendo del prefijo del operando
        if operando.startswith('#'):
            n, i = 0, 0  # Inmediato
        elif operando.startswith('@'):
            n, i = 1, 0  # Indirecto

        if usar_extendido:
            x = 1  # Activar bandera de extensión

        if formato == 3:
            desplazamiento = direccion - (contador_loc + 3)
            if -2048 <= desplazamiento <= 2047:
                p = 1  # Uso de desplazamiento relativo
            else:
                b = 1  # Uso de la base (en caso de ser necesario)

        elif formato == 4:
            e = 1  # Formato extendido
            # Generar el registro de modificación
            registros_modificacion.append(generar_registro_modificacion(contador_loc + 1))

        # Armar el código objeto
        codigo_objeto = (codigo_operacion << 16) | (n << 17) | (i << 16) | (x << 15) | (b << 14) | (p << 13) | (e << 12) | (direccion & 0xFFF)

        return f"{codigo_objeto:06X}", "Absoluto"  # Devolver como absoluto para mantener consistencia

    return '', "Error: Instrucción no soportada"


def escribir_archivo_salida(text_widget, lineas_procesadas, tabla_simbolos, registros_modificacion, codigos_texto, registro_encabezado, registro_fin, tabla_bloques):
    text_widget.delete(1.0, tk.END)  # Limpiar el contenido del text_widget antes de escribir
    
    # Escribir archivo intermedio
    text_widget.insert(tk.END, "Archivo Intermedio:\n")
    text_widget.insert(tk.END, "CP".ljust(8) + "Etiqueta".ljust(12) + "Instrucción".ljust(12) + "Operando".ljust(12) + "Bloque".ljust(8) + "Código Objeto".ljust(12) + "   Errores".ljust(12) + "\n")
    text_widget.insert(tk.END, "="*80 + "\n")
    
    for linea in lineas_procesadas:
        if 'Error' in linea:
            text_widget.insert(tk.END, f"{linea.get('CP', '').ljust(8)}{linea.get('Etiqueta', '').ljust(12)}{linea.get('Instrucción', '').ljust(12)}{linea.get('Operando', '').ljust(12)}{linea.get('Bloque', '').ljust(8)}{linea.get('Código Objeto', '').ljust(12)}{linea['Error'].ljust(12)}\n")
        else:
            text_widget.insert(tk.END, f"{linea['CP'].ljust(8)}{linea['Etiqueta'].ljust(12)}{linea['Instrucción'].ljust(12)}{linea['Operando'].ljust(12)}{linea['Bloque'].ljust(8)}{linea['Código Objeto'].ljust(12)}{'':<12}\n")
    
    # Tabla de símbolos
    text_widget.insert(tk.END, "\nTabla de Símbolos:\n")
    text_widget.insert(tk.END, "Símbolo".ljust(12) + "Dirección".ljust(12) + "Tipo".ljust(12) + "Bloque\n")
    text_widget.insert(tk.END, "="*40 + "\n")
    
    for simbolo, (direccion, tipo, bloque) in tabla_simbolos.items():
        direccion_formateada = hex(direccion)[2:].upper().zfill(4)
        text_widget.insert(tk.END, f"{simbolo.ljust(12)}{direccion_formateada.ljust(12)}{tipo.ljust(12)}{bloque}\n")
    
    # Tabla de bloques
    text_widget.insert(tk.END, "\nTabla de Bloques:\n")
    text_widget.insert(tk.END, "Bloque".ljust(12) + "Número".ljust(12) + "LOCCTR Inicial".ljust(16) + "Tamaño\n")
    text_widget.insert(tk.END, "="*52 + "\n")
    
    for bloque, info in tabla_bloques.items():
        numero_bloque = str(info['NUMERO'])
        locctr_inicial = hex(info['LOCCTR'])[2:].upper().zfill(4)
        tamano = hex(info['TAMANO'])[2:].upper().zfill(4)
        text_widget.insert(tk.END, f"{bloque.ljust(12)}{numero_bloque.ljust(12)}{locctr_inicial.ljust(16)}{tamano}\n")
    
    # Tamaño total del programa
    tamano_total = sum(info['TAMANO'] for info in tabla_bloques.values())
    text_widget.insert(tk.END, "\nTamaño total del programa: " + hex(tamano_total)[2:].upper().zfill(4) + " bytes\n")

    # Escribir registros de encabezado, texto y fin
    text_widget.insert(tk.END, "\nRegistros de objeto:\n")
    text_widget.insert(tk.END, f"{registro_encabezado}\n")
    for registro in codigos_texto:
        text_widget.insert(tk.END, f"{registro}\n")
    for registro in registros_modificacion:
        text_widget.insert(tk.END, f"{registro}\n")
    text_widget.insert(tk.END, f"{registro_fin}\n")

def leer_archivo_entrada(ruta_archivo):
    with open(ruta_archivo, 'r') as archivo:
        return archivo.readlines()

def abrir_archivo(text_widget):
    ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
    if ruta_archivo:
        with open(ruta_archivo, 'r') as archivo:
            contenido = archivo.read()
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, contenido)

def guardar_archivo(text_widget):
    ruta_archivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")])
    if ruta_archivo:
        with open(ruta_archivo, 'w') as archivo:
            archivo.write(text_widget.get(1.0, tk.END))

def ensamblador(text_widget_entrada):
    # Crear una nueva ventana para la salida
    ventana_salida = tk.Toplevel()
    ventana_salida.title("Resultados del Ensamblador")
    
    # Crear un widget de texto en la nueva ventana para mostrar la salida
    text_widget_salida = tk.Text(ventana_salida, wrap=tk.NONE)
    text_widget_salida.pack(fill=tk.BOTH, expand=True)
    
    # Obtener el contenido del widget de entrada y dividirlo en líneas
    lineas = text_widget_entrada.get("1.0", tk.END).strip().splitlines()
    
    registros_modificacion = []
    codigos_texto = []
    codigos_objeto = []
    lineas_procesadas = []
    contador_loc = 0x0000 
    bloque_actual = 'DEFAULT'
    inicio_programa = contador_loc
    nombre_programa = None
    global nombre_programa_global

    # Verifica la primera línea para obtener el nombre del programa
    if lineas:
        primera_linea = lineas[0].split()
        if len(primera_linea) == 3 and primera_linea[1] == 'START':
            nombre_programa = primera_linea[0][:6].ljust(6)
            nombre_programa_global = primera_linea[0][:6].ljust(6)

    for linea in lineas:
        resultado = procesar_linea(linea, contador_loc, tabla_simbolos, registros_modificacion, codigos_texto, codigos_objeto, tabla_bloques)
        if 'Error' not in resultado:
            lineas_procesadas.append(resultado)
            
            formato = TABOP.get(resultado['Instrucción'], [None, None])[1]
            
            if resultado['Instrucción'] == 'RESB':
                # Incrementar contador_loc según el operando
                try:
                    valor_resb = int(resultado['Operando'])  # Obtener el operando como entero
                    contador_loc += valor_resb  # Incrementar el CP
                except ValueError:
                    resultado['Error'] = "Error: Operando inválido para RESB"
                    lineas_procesadas.append(resultado)
                    continue
                
            elif resultado['Instrucción'] == 'RESW':
                # Incrementar contador_loc según el operando multiplicado por 3
                try:
                    valor_resw = int(resultado['Operando']) * 3  # Multiplicar por 3
                    contador_loc += valor_resw  # Incrementar el CP
                except ValueError:
                    resultado['Error'] = "Error: Operando inválido para RESW"
                    lineas_procesadas.append(resultado)
                    continue
            
            else:
                if formato == 1:
                    contador_loc += 1
                elif formato == 2:
                    contador_loc += 2
                elif formato == 3 or formato == 4:
                    contador_loc += 3 if formato == 3 else 4
            
            # Actualizar el LOCCTR del bloque actual
            tabla_bloques[bloque_actual]['LOCCTR'] = contador_loc
        else:
            resultado['Instrucción'] = linea.split()[0]  
            lineas_procesadas.append(resultado)

    # Inicializar una variable para rastrear el LOCCTR acumulado
    locctr_acumulado = 0

    for bloque, info in tabla_bloques.items():
        # Calcular el tamaño del bloque actual
        if locctr_acumulado == 0:
            # Primer bloque, simplemente calcular el tamaño
            info['TAMANO'] = info['LOCCTR'] - info.get('BASE', 0)
        else:
            # Bloques subsiguientes, sumar al LOCCTR acumulado el tamaño del bloque anterior
            info['TAMANO'] = info['LOCCTR'] - info.get('BASE', 0)  # Calcular el tamaño del bloque
            info['LOCCTR'] += locctr_acumulado  # Sumar el tamaño del bloque anterior al LOCCTR del bloque actual

        # Actualizar el LOCCTR acumulado
        locctr_acumulado += info['TAMANO']

    # Generar el encabezado y fin
    if codigos_objeto:
        registro_texto = generar_registro_texto(contador_loc, ''.join(codigos_objeto))
        codigos_texto.append(registro_texto)

    # Usar el nombre del programa si fue detectado; de lo contrario, usar "PROG" por defecto
    nombre_programa = nombre_programa if nombre_programa else "PROG".ljust(6)
    
    registro_encabezado = generar_registro_encabezado(nombre_programa, inicio_programa, contador_loc - inicio_programa)
    registro_fin = generar_registro_fin(inicio_programa)

    # Escribir el archivo de salida en el widget de salida
    text_widget_salida.delete("1.0", tk.END)  # Limpiar el contenido antes de escribir
    escribir_archivo_salida(text_widget_salida, lineas_procesadas, tabla_simbolos, registros_modificacion, codigos_texto, registro_encabezado, registro_fin, tabla_bloques)


def crear_editor():
    root = tk.Tk()
    root.title("Editor de Ensamblador")
    
    editor = EditorConNumerosLinea(root)
    
    # Crear menú
    menu = tk.Menu(root)
    root.config(menu=menu)
    
    archivo_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Archivo", menu=archivo_menu)
    archivo_menu.add_command(label="Abrir", command=lambda: abrir_archivo(editor.text_widget))
    archivo_menu.add_command(label="Guardar", command=lambda: guardar_archivo(editor.text_widget))
    archivo_menu.add_separator()
    archivo_menu.add_command(label="Salir", command=root.quit)
    
    ensamblador_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Ensamblador", menu=ensamblador_menu)
    ensamblador_menu.add_command(label="Ejecutar Ensamblador", command=lambda: ensamblador(editor.text_widget))
    
    root.mainloop()

# Ejecutar el editor
crear_editor()