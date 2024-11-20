import tkinter as tk
from tkinter import ttk, filedialog
import re

class SIC_XE_Loader:
    def __init__(self, dirprog=0x0000, dirini=0x0000):
        self.TABSE = {}
        self.MEMORY = [0xFF] * (0xFFFF + 1)  # 64KB de memoria inicializada a 0xFF
        self.DIRPROG = dirprog  # Dirección inicial del programa
        self.DIRINI = dirini  # Dirección inicial del programa
        self.DIRFIN = 0x0000
        self.root = None
        self.dirprog_var = None  # Variable para la dirección inicial

    def process_pass1(self, records):
        dirsc = self.DIRPROG  # Usar la dirección inicial proporcionada por el usuario
        section_name = None  # Nombre de la sección actual

        for record in records:
            record = record.strip()  # Limpiar la línea
            if not record:
                continue  # Ignorar líneas vacías

            if record.startswith('H'):  # Registro de encabezado
                print(f"Encabezado: {record}")
                section_name = record[1:7].strip()
                dirsc = self.DIRPROG
                length = int(record[13:19], 16)
                if section_name in self.TABSE:
                    print(f"Error: Símbolo externo duplicado: {section_name}")
                else:
                    print("DIRECCION H: ", dirsc)
                    self.TABSE[section_name] = {'direccion': dirsc, 'longitud': length}

            elif record.startswith('D') and dirsc is not None:  # Registro de definición
                print(f"Procesando registro D: {record}")
                data = record[1:]  # Omitir el carácter 'D'
                while data:
                    symbol = data[:6].split()[0]
                    data = data[len(symbol):].lstrip()  # Avanzar al siguiente bloque de datos
                    if len(data) < 6:  # Verificar que haya al menos 6 caracteres restantes para la dirección
                        print(f"Error: Dirección incompleta en registro D: {record}")
                        break
                    addr = data[:6]  # Leer la dirección relativa (6 caracteres)
                    data = data[6:].lstrip()  # Avanzar al siguiente símbolo y dirección

                    try:
                        if len(addr) != 6 or not all(c in "0123456789ABCDEF" for c in addr):
                            raise ValueError(f"Dirección inválida: '{addr}'")
                        address = dirsc + int(addr, 16)
                        if symbol in self.TABSE:
                            print(f"Error: Símbolo externo duplicado: {symbol}")
                        else:
                            print(f"Definiendo {symbol} en {address:04X}")
                            self.TABSE[symbol] = {'direccion': address}
                    except ValueError as e:
                        print(f"Error procesando símbolo {symbol}: {e}")
                        continue

            elif record.startswith('E') and dirsc is not None:  # Registro de fin
                self.DIRPROG += self.TABSE.get(section_name, {}).get('longitud', 0)
                print(f"Fin del programa. Nueva dirsc: {self.DIRPROG:04X}")
                self.DIRFIN = self.DIRPROG
                print(f"DIRFIN: {self.DIRFIN:04X}")

    def process_pass2(self, records):
        dirsc = self.DIRPROG  # Dirección de inicio de la sección de control
        self.DIRFIN = self.DIRPROG

        for record in records:
            if record.startswith('H'):  # Registro de encabezado
                section_name = record[1:7].strip()
                dirsc = self.TABSE.get(section_name, {}).get('direccion', self.DIRPROG)

            elif record.startswith('T') and dirsc is not None:  # Registro de texto
                start = dirsc + int(record[1:7], 16)  # Dirección inicial del registro
                length = int(record[7:9], 16)  # Longitud en bytes
                data = re.findall(r'\w{2}', record[9:])  # Extrae pares hexadecimales

                for i, byte in enumerate(data[:length]):  # Limitarse a los bytes definidos por la longitud
                    self.MEMORY[start + i] = int(byte, 16)
                
                self.DIRFIN = max(self.DIRFIN, start + length - 1)

            elif record.startswith('M') and dirsc is not None:  # Registro de modificación
                address = dirsc + int(record[1:7], 16)  # Dirección a modificar
                length = int(record[7:9], 16)  # Longitud en medios bytes
                operation = record[9]  # '+' o '-'
                symbol = record[10:].strip()  # Símbolo externo

                if symbol in self.TABSE:
                    value = self.TABSE[symbol]['direccion']
                    self.DIRFIN = max(self.DIRFIN, address + (length + 1) // 2 - 1)

                    current_value = int(''.join(f"{self.MEMORY[address + i]:02X}" for i in range((length + 1) // 2)), 16)

                    if operation == '+':
                        new_value = current_value + value
                    elif operation == '-':
                        new_value = current_value - value
                    else:
                        print(f"Error: Operación desconocida '{operation}' en registro M")
                        continue

                    new_value_hex = f"{new_value:0{(length + 1) // 2 * 2}X}"
                    for i in range(0, len(new_value_hex), 2):
                        self.MEMORY[address + i // 2] = int(new_value_hex[i:i+2], 16)
                else:
                    print(f"Error: Símbolo indefinido {symbol}")

            elif record.startswith('E'):  # Registro de fin
                if record[1:7].strip():  # Si hay una dirección especificada
                    dirsc += int(record[1:7], 16)

        print("Paso 2 completado.")

    def create_tabse_table(self, root):
        frame = ttk.Frame(root)
        frame.pack(pady=10)
        ttk.Label(frame, text="TABSE", font=("Arial", 12, "bold")).grid(row=0, columnspan=3)

        columns = ('Símbolo', 'Dirección', 'Longitud')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        for sym, data in self.TABSE.items():
            tree.insert('', tk.END, values=(sym, f"{data['direccion']:04X}", f"{data.get('longitud', 0):04X}"))

        tree.grid(row=1, column=0, columnspan=3)

    # Esta función imprime solamente las filas que tienen datos y omite las que no tienen (FF).
    # def create_memory_map(self, root, dirprog, dirfin, memory):
    #     frame = ttk.Frame(root)
    #     frame.pack(pady=10)
    #     ttk.Label(frame, text="Mapa de Memoria", font=("Arial", 12, "bold")).grid(row=0, columnspan=18)

    #     # Encabezados de las columnas: Dirección y 16 columnas hexadecimales
    #     columns = ['Dirección'] + [f"{i:X}" for i in range(16)]
    #     tree = ttk.Treeview(frame, columns=columns, show='headings')

    #     for col in columns:
    #         tree.heading(col, text=col)
    #         width = 80 if col == 'Dirección' else 30
    #         tree.column(col, width=width)

    #     # Scrollbars
    #     vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    #     hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    #     tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    #     # Posicionar los scrollbars
    #     tree.grid(row=1, column=0, columnspan=17, sticky="nsew")
    #     vsb.grid(row=1, column=17, sticky="ns")
    #     hsb.grid(row=2, column=0, columnspan=17, sticky="ew")

    #     # Expandir adecuadamente la tabla al redimensionar la ventana
    #     frame.grid_rowconfigure(1, weight=1)
    #     frame.grid_columnconfigure(0, weight=1)

    #     # Validar los límites del rango de direcciones
    #     dirprog = max(0, dirprog)
    #     dirfin = min(len(memory) - 1, dirfin)

    #     # Insertar filas para el rango especificado
    #     for addr in range(dirprog, dirfin + 1, 16):  # Incrementos de 16 bytes por fila
    #         row_data = [f"{memory[addr + i]:02X}" if addr + i <= dirfin else "--" for i in range(16)]
            
    #         # Verificar si la fila contiene solo 'FF'
    #         if all(byte == "FF" for byte in row_data if byte != "--"):
    #             continue  # Omitir filas con solo 'FF'
            
    #         tree.insert('', tk.END, values=[f"{addr:04X}"] + row_data)

    # Esta función imprime todas las filas, incluso las que tienen 'FF' con un scroll.
    def create_memory_map(self, root, dirprog, dirfin, memory):
        frame = ttk.Frame(root)
        frame.pack(pady=10)
        ttk.Label(frame, text="Mapa de Memoria", font=("Arial", 12, "bold")).grid(row=0, columnspan=18)

        # Encabezados de las columnas: Dirección y 16 columnas hexadecimales
        columns = ['Dirección'] + [f"{i:X}" for i in range(16)]
        tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col)
            width = 80 if col == 'Dirección' else 30
            tree.column(col, width=width)

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Posicionar los scrollbars
        tree.grid(row=1, column=0, columnspan=17, sticky="nsew")
        vsb.grid(row=1, column=17, sticky="ns")
        hsb.grid(row=2, column=0, columnspan=17, sticky="ew")

        # Expandir adecuadamente la tabla al redimensionar la ventana
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Validar los límites del rango de direcciones
        dirprog = max(0, dirprog)
        dirfin = min(len(memory) - 1, dirfin)

        # Insertar filas para el rango especificado
        for addr in range(dirprog, dirfin + 1, 16):  # Incrementos de 16 bytes por fila
            row_data = [f"{memory[addr + i]:02X}" if addr + i <= dirfin else "--" for i in range(16)]
            tree.insert('', tk.END, values=[f"{addr:04X}"] + row_data)


    def load_file(self):  
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                records = file.read().strip().split('\n')
                self.process_pass1(records)
                self.process_pass2(records)
            self.update_gui()

    def update_gui(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.create_tabse_table(self.content_frame)
        dirprog = int(self.dirprog_var.get(), 16)
        dirfin = int(self.DIRFIN)
        self.create_memory_map(self.content_frame, dirprog, dirfin, self.MEMORY)

    def run_gui(self):
        self.root = tk.Tk()
        self.root.title("Cargador Ligador SIC/XE")
        self.root.geometry("800x600")

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
    
        archivo_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Cargar programa", command=self.load_file)

        ttk.Label(self.root, text=f"Dirección Inicial (Hex): " f"{self.DIRPROG:04X}").pack(pady=10)
        self.dirprog_var = tk.StringVar(value=f"{self.DIRPROG:04X}")
        
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill="both", expand=True)

        self.root.mainloop()

if __name__ == "__main__":
    loader = SIC_XE_Loader()
    loader.run_gui()