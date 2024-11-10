import tkinter as tk

class EnsambladorApp:
    def __init__(self, tabla_simbolos, tabla_bloques, tabop):
        self.tabla_simbolos = tabla_simbolos
        self.tabla_bloques = tabla_bloques
        self.TABOP = tabop  # Tabla de operaciones

    def ensamblar(self, text_widget_entrada):
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
        contador_loc = 0x1000 
        bloque_actual = 'DEFAULT'
        inicio_programa = contador_loc
        nombre_programa = None

        # Verifica la primera línea para obtener el nombre del programa
        if lineas:
            primera_linea = lineas[0].split()
            if len(primera_linea) == 3 and primera_linea[1] == 'START':
                nombre_programa = primera_linea[0][:6].ljust(6)

        for linea in lineas:
            resultado = self.procesar_linea(linea, contador_loc, registros_modificacion, codigos_texto, codigos_objeto)

            if 'Error' not in resultado:
                lineas_procesadas.append(resultado)
                
                formato = self.TABOP.get(resultado['Instrucción'], [None, None])[1]
                
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
                self.tabla_bloques[bloque_actual]['LOCCTR'] = contador_loc
            else:
                resultado['Instrucción'] = linea.split()[0]  
                lineas_procesadas.append(resultado)

        # Inicializar una variable para rastrear el LOCCTR acumulado
        locctr_acumulado = 0

        for bloque, info in self.tabla_bloques.items():
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
            registro_texto = self.generar_registro_texto(contador_loc, ''.join(codigos_objeto))
            codigos_texto.append(registro_texto)

        # Usar el nombre del programa si fue detectado; de lo contrario, usar "PROG" por defecto
        nombre_programa = nombre_programa if nombre_programa else "PROG".ljust(6)
        
        registro_encabezado = self.generar_registro_encabezado(nombre_programa, inicio_programa, contador_loc - inicio_programa)
        registro_fin = self.generar_registro_fin(inicio_programa)

        # Escribir el archivo de salida en el widget de salida
        text_widget_salida.delete("1.0", tk.END)  # Limpiar el contenido antes de escribir
        self.escribir_archivo_salida(text_widget_salida, lineas_procesadas, registros_modificacion, codigos_texto, registro_encabezado, registro_fin)
