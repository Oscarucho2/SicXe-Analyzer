class GeneradorRegistros:
    def generar_registro_encabezado(self, nombre_programa, inicio, longitud):
        """Genera un registro de encabezado."""
        return f"H{nombre_programa[:6].ljust(6)}{inicio:06X}{longitud:06X}"

    def generar_registro_texto(self, inicio, codigos_objeto):
        """Genera un registro de texto."""
        longitud = len(codigos_objeto) // 2
        return f"T{inicio:06X}{longitud:02X}{codigos_objeto}"

    def generar_registro_modificacion(self, direccion):
        """Genera un registro de modificación."""
        return f"M{direccion:06X}05"  # Longitud 5 bytes para formato 4

    def generar_registro_fin(self, inicio):
        """Genera un registro de fin."""
        return f"E{inicio:06X}"
