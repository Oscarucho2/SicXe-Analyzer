import re

class EvaluadorExpresion:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos  # Tabla de símbolos a usar para evaluar las expresiones

    def evaluar(self, expresion):
        # Tokenizamos la expresión, separando números, operadores y paréntesis
        tokens = re.findall(r'[A-Za-z_]\w*|[+\-*/()]|\d+', expresion)
        
        # Inicializamos las pilas para la evaluación
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
                if token not in self.tabla_simbolos:
                    raise ValueError(f"Símbolo no reconocido: {token}")

                # Obtenemos el valor y tipo de dirección del símbolo
                valor, tipo = self.tabla_simbolos[token]
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
                    pila_tipos.append('A')
                pila_operadores.pop()  # Quitamos el '('
            elif token in '+-*/':  # Si es un operador
                while (pila_operadores and pila_operadores[-1] in '+-*/' and
                       pila_operadores[-1] != '(' and pila_operadores[-1] != '('):
                    operador = pila_operadores.pop()
                    b = pila_valores.pop()
                    a = pila_valores.pop()
                    tipo_b = pila_tipos.pop()
                    tipo_a = pila_tipos.pop()
                    pila_valores.append(aplicar_operador(operador, b, a))
                    pila_tipos.append('A')
                pila_operadores.append(token)
            else:
                raise ValueError(f"Símbolo o operador no reconocido: {token}")

        # Procesamos los operadores restantes
        procesar_pila()

        if len(pila_valores) != 1:
            raise ValueError("Error en la evaluación de la expresión")

        valor_final = pila_valores[0]
        tipo_direccion = 'relativo' if 'R' in pila_tipos else 'absoluto'

        return valor_final, tipo_direccion
