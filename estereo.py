"""
Fichero: estereo.py
Alumno: Steven Daniel Vizcaino Cedeño
Descripción: Tratamiento de señal estéreo a bajo nivel manipulando cabeceras
             y datos en ficheros WAVE utilizando únicamente la biblioteca struct.
"""

import struct

def leer_riff_wave(f):
    """
    Función auxiliar para leer e interpretar la cabecera de un fichero WAVE.
    Soporta ficheros con subcachos intermedios buscando activamente 'fmt ' y 'data'.
    
    Retorna:
        fmt_info (dict): Información del subcacho 'fmt '.
        data_size (int): Tamaño del subcacho de datos en bytes.
        data_offset (int): Posición en bytes donde comienzan las muestras de audio.
    """
    riff_header = f.read(12)
    if len(riff_header) < 12:
        raise ValueError("Cabecera RIFF incompleta o corrupta.")
        
    chunk_id, chunk_size, format_tag = struct.unpack('<4sI4s', riff_header)
    if chunk_id != b'RIFF' or format_tag != b'WAVE':
        raise ValueError("El fichero no es un archivo WAVE RIFF válido.")
        
    fmt_info = None
    data_size = None
    data_offset = None
    
    # Buscamos de manera dinámica los bloques 'fmt ' y 'data'
    while True:
        chunk_header = f.read(8)
        if len(chunk_header) < 8:
            break
        subchunk_id, subchunk_size = struct.unpack('<4sI', chunk_header)
        
        if subchunk_id == b'fmt ':
            fmt_data = f.read(16)
            if len(fmt_data) < 16:
                raise ValueError("Subcacho 'fmt ' incompleto.")
            audio_format, num_channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack('<HHIIHH', fmt_data)
            
            # Saltamos cualquier byte adicional en caso de que fmt tenga tamaño extendido
            if subchunk_size > 16:
                f.read(subchunk_size - 16)
                
            fmt_info = {
                "audio_format": audio_format,
                "num_channels": num_channels,
                "sample_rate": sample_rate,
                "byte_rate": byte_rate,
                "block_align": block_align,
                "bits_per_sample": bits_per_sample
            }
        elif subchunk_id == b'data':
            data_size = subchunk_size
            data_offset = f.tell()
            break
        else:
            # Saltamos bloques no deseados (ej. LIST, JUNK, bext)
            f.seek(subchunk_size, 1)
            
    if not fmt_info:
        raise ValueError("Falta el subcacho obligatorio 'fmt '.")
    if data_size is None:
        raise ValueError("Falta el subcacho obligatorio 'data'.")
        
    return fmt_info, data_size, data_offset


def escribir_cabecera(f, num_channels, sample_rate, bits_per_sample, data_size):
    """
    Escribe una cabecera canónica WAVE PCM de 44 bytes en el fichero binario 'f'.
    """
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    chunk_size = 36 + data_size
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
                         b'RIFF', chunk_size, b'WAVE',
                         b'fmt ', 16, 1, num_channels,
                         sample_rate, byte_rate, block_align, bits_per_sample,
                         b'data', data_size)
    f.write(header)


def estereo2mono(ficEste, ficMono, canal=2):
    """
    Lee un archivo estéreo de 16 bits y genera un archivo mono según el canal especificado:
        canal=0: Canal Izquierdo (L)
        canal=1: Canal Derecho (R)
        canal=2: Semisuma (L + R) // 2
        canal=3: Semidiferencia (L - R) // 2
    """
    if canal not in (0, 1, 2, 3):
        raise ValueError("Canal no válido. Debe ser 0 (L), 1 (R), 2 (semisuma) o 3 (semidiferencia).")
        
    with open(ficEste, 'rb') as f_in:
        fmt, data_size, data_offset = leer_riff_wave(f_in)
        
        if fmt["num_channels"] != 2:
            raise ValueError("El archivo de entrada debe ser estéreo (2 canales).")
        if fmt["bits_per_sample"] != 16:
            raise ValueError("El archivo debe tener muestras codificadas en 16 bits.")
            
        f_in.seek(data_offset)
        raw_data = f_in.read(data_size)
        
    # Unpack completo usando comprensiones y struct sin usar bucles tradicionales
    num_muestras = data_size // 2
    muestras = struct.unpack(f'<{num_muestras}h', raw_data)
    
    # Separamos canales usando rodajas (slicing)
    L = muestras[0::2]
    R = muestras[1::2]
    
    # Operaciones vectorizadas con comprensiones de listas
    if canal == 0:
        muestras_mono = L
    elif canal == 1:
        muestras_mono = R
    elif canal == 2:
        muestras_mono = [(l + r) // 2 for l, r in zip(L, R)]
    elif canal == 3:
        muestras_mono = [(l - r) // 2 for l, r in zip(L, R)]
        
    # Empaquetamos y escribimos el nuevo fichero
    data_out = struct.pack(f'<{len(muestras_mono)}h', *muestras_mono)
    
    with open(ficMono, 'wb') as f_out:
        escribir_cabecera(f_out, num_channels=1, sample_rate=fmt["sample_rate"], 
                          bits_per_sample=16, data_size=len(data_out))
        f_out.write(data_out)


def mono2estereo(ficIzq, ficDer, ficEste):
    """
    Combina dos archivos mono de 16 bits para crear un archivo estéreo de 16 bits.
    """
    with open(ficIzq, 'rb') as f_izq, open(ficDer, 'rb') as f_der:
        fmt_izq, size_izq, offset_izq = leer_riff_wave(f_izq)
        fmt_der, size_der, offset_der = leer_riff_wave(f_der)
        
        # Validaciones de formato
        if fmt_izq["num_channels"] != 1 or fmt_der["num_channels"] != 1:
            raise ValueError("Ambos ficheros de entrada deben ser monofónicos.")
        if fmt_izq["sample_rate"] != fmt_der["sample_rate"]:
            raise ValueError("La frecuencia de muestreo de ambos ficheros debe ser la misma.")
        if size_izq != size_der:
            raise ValueError("Ambos ficheros deben tener la misma cantidad de muestras.")
            
        f_izq.seek(offset_izq)
        f_der.seek(offset_der)
        raw_izq = f_izq.read(size_izq)
        raw_der = f_der.read(size_der)
        
    num_muestras = size_izq // 2
    L = struct.unpack(f'<{num_muestras}h', raw_izq)
    R = struct.unpack(f'<{num_muestras}h', raw_der)
    
    # Intercalamos L y R de forma eficiente
    muestras_estereo = [val for par in zip(L, R) for val in par]
    data_out = struct.pack(f'<{len(muestras_estereo)}h', *muestras_estereo)
    
    with open(ficEste, 'wb') as f_out:
        escribir_cabecera(f_out, num_channels=2, sample_rate=fmt_izq["sample_rate"],
                          bits_per_sample=16, data_size=len(data_out))
        f_out.write(data_out)


def codEstereo(ficEste, ficCod):
    """
    Codifica un fichero estéreo de 16 bits en uno de 32 bits (mono) donde:
        - Los 16 bits más significativos contienen la semisuma (S)
        - Los 16 bits menos significativos contienen la semidiferencia (D)
    """
    with open(ficEste, 'rb') as f_in:
        fmt, data_size, data_offset = leer_riff_wave(f_in)
        
        if fmt["num_channels"] != 2:
            raise ValueError("El fichero de entrada debe ser estéreo.")
        if fmt["bits_per_sample"] != 16:
            raise ValueError("El fichero de entrada debe ser de 16 bits.")
            
        f_in.seek(data_offset)
        raw_data = f_in.read(data_size)
        
    num_muestras = data_size // 2
    muestras = struct.unpack(f'<{num_muestras}h', raw_data)
    
    L = muestras[0::2]
    R = muestras[1::2]
    
    S = [(l + r) // 2 for l, r in zip(L, R)]
    D = [(l - r) // 2 for l, r in zip(L, R)]
    
    # Empaquetamos S en la parte alta y D (enmascarado a 16 bits sin signo) en la parte baja
    muestras_32 = [(s << 16) | (d & 0xFFFF) for s, d in zip(S, D)]
    data_out = struct.pack(f'<{len(muestras_32)}i', *muestras_32)
    
    with open(ficCod, 'wb') as f_out:
        escribir_cabecera(f_out, num_channels=1, sample_rate=fmt["sample_rate"],
                          bits_per_sample=32, data_size=len(data_out))
        f_out.write(data_out)


def decEstereo(ficCod, ficEste):
    """
    Decodifica un fichero de 32 bits codificado a estéreo de 16 bits.
    """
    with open(ficCod, 'rb') as f_in:
        fmt, data_size, data_offset = leer_riff_wave(f_in)
        
        if fmt["num_channels"] != 1:
            raise ValueError("El fichero codificado debe ser monofónico de 32 bits.")
        if fmt["bits_per_sample"] != 32:
            raise ValueError("Se requiere un fichero codificado en 32 bits.")
            
        f_in.seek(data_offset)
        raw_data = f_in.read(data_size)
        
    num_muestras = data_size // 4
    muestras_32 = struct.unpack(f'<{num_muestras}i', raw_data)
    
    # Extraemos la semisuma (con extensión de signo mediante desplazamiento aritmético)
    S = [val >> 16 for val in muestras_32]
    
    # Extraemos la semidiferencia enmascarada y corregimos el signo para 16 bits signed
    D_raw = [val & 0xFFFF for val in muestras_32]
    D = [d if d < 32768 else d - 65536 for d in D_raw]
    
    # Reconstrucción matemática de los canales originales L y R
    # Limitamos los valores al rango seguro de enteros de 16 bits con signo [-32768, 32767]
    L = [max(-32768, min(32767, s + d)) for s, d in zip(S, D)]
    R = [max(-32768, min(32767, s - d)) for s, d in zip(S, D)]
    
    # Intercalamos canales para generar la trama de muestras estéreo
    muestras_estereo = [val for par in zip(L, R) for val in par]
    data_out = struct.pack(f'<{len(muestras_estereo)}h', *muestras_estereo)
    
    with open(ficEste, 'wb') as f_out:
        escribir_cabecera(f_out, num_channels=2, sample_rate=fmt["sample_rate"],
                          bits_per_sample=16, data_size=len(data_out))
        f_out.write(data_out)
