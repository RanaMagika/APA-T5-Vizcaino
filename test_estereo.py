"""
Fichero: test_estereo.py
Descripción: Script de pruebas para verificar el correcto funcionamiento 
             de las funciones de procesamiento de audio en estereo.py.
"""

import os
from estereo import estereo2mono, mono2estereo, codEstereo, decEstereo, leer_riff_wave

def probar_practica():
    # Rutas de los ficheros de prueba
    origen = "wav/komm.wav"
    mono_izq = "wav/komm_L.wav"
    mono_der = "wav/komm_R.wav"
    mono_semisuma = "wav/komm_semisuma.wav"
    mono_semidif = "wav/komm_semidiferencia.wav"
    estereo_reconstruido = "wav/komm_reconstruido.wav"
    fichero_codificado_32 = "wav/komm_cod32.wav"
    estereo_decodificado_32 = "wav/komm_dec32.wav"

    print("==================================================")
    print("      INICIANDO PRUEBAS DE AUDIO ESTÉREO          ")
    print("==================================================")

    # Verificar que el fichero origen existe
    if not os.path.exists(origen):
        print(f" Error: No se encuentra el archivo original en: {origen}")
        print("Asegúrate de haber creado la carpeta 'wav' y guardado 'komm.wav' dentro.")
        return

    print(f"🎵 Fichero original detectado: {origen}")
    
    # -------------------------------------------------------------
    # PRUEBA 1: Estéreo a Mono (canales individuales, semisuma y semidiferencia)
    # -------------------------------------------------------------
    print("\n--- [Prueba 1] Separando canales estéreo a mono... ---")
    try:
        # Extraer canal izquierdo (0)
        estereo2mono(origen, mono_izq, canal=0)
        print("   Canal izquierdo (L) extraído correctamente.")
        
        # Extraer canal derecho (1)
        estereo2mono(origen, mono_der, canal=1)
        print("   Canal derecho (R) extraído correctamente.")
        
        # Extraer semisuma (2) - por defecto
        estereo2mono(origen, mono_semisuma, canal=2)
        print("   Canal Semisuma (L+R)/2 extraído correctamente.")
        
        # Extraer semidiferencia (3)
        estereo2mono(origen, mono_semidif, canal=3)
        print("   Canal Semidiferencia (L-R)/2 extraído correctamente.")
        
    except Exception as e:
        print(f"   Error en Prueba 1: {e}")
        return

    # -------------------------------------------------------------
    # PRUEBA 2: Mono a Estéreo (Reconstrucción desde L y R)
    # -------------------------------------------------------------
    print("\n--- [Prueba 2] Reconstruyendo estéreo desde L y R... ---")
    try:
        mono2estereo(mono_izq, mono_der, estereo_reconstruido)
        print("  Fichero estéreo reconstruido con éxito.")
        
        # Verificaciones rápidas de tamaño
        tam_origen = os.path.getsize(origen)
        tam_nuevo = os.path.getsize(estereo_reconstruido)
        print(f"   Tamaño original: {tam_origen} bytes")
        print(f"   Tamaño reconstruido: {tam_nuevo} bytes")
        if abs(tam_origen - tam_nuevo) < 100:  # Margen por pequeñas variaciones de metadatos/bext
            print("   ¡Excelente! Los tamaños coinciden casi perfectamente.")
        else:
            print("   Advertencia: Los tamaños difieren, comprueba las cabeceras.")
            
    except Exception as e:
        print(f"   Error en Prueba 2: {e}")
        return

    # -------------------------------------------------------------
    # PRUEBA 3: Codificación de 16 bits estéreo a 32 bits mono
    # -------------------------------------------------------------
    print("\n--- [Prueba 3] Codificando en 32 bits (S_MSB + D_LSB)... ---")
    try:
        codEstereo(origen, fichero_codificado_32)
        print("   Fichero de 32 bits generado correctamente.")
        
        # Comprobar cabecera del fichero codificado
        with open(fichero_codificado_32, 'rb') as f:
            fmt, _, _ = leer_riff_wave(f)
            print(f"   Formato codificado: {fmt['bits_per_sample']} bits, {fmt['num_channels']} canal(es).")
            
    except Exception as e:
        print(f"   Error en Prueba 3: {e}")
        return

    # -------------------------------------------------------------
    # PRUEBA 4: Decodificación de 32 bits a 16 bits estéreo
    # -------------------------------------------------------------
    print("\n--- [Prueba 4] Decodificando fichero de 32 bits... ---")
    try:
        decEstereo(fichero_codificado_32, estereo_decodificado_32)
        print("   Fichero estéreo recuperado desde los 32 bits con éxito.")
        
        tam_dec = os.path.getsize(estereo_decodificado_32)
        print(f"   Tamaño decodificado: {tam_dec} bytes")
        
    except Exception as e:
        print(f"   Error en Prueba 4: {e}")
        return

    print("\n==================================================")
    print("        ¡TODOS LOS TESTS COMPLETADOS!           ")
    print("==================================================")
    print("Prueba a escuchar los archivos generados en la carpeta 'wav/':")
    print("  - komm_L.wav: Solo se deberían escuchar las voces y palmas (izquierda).")
    print("  - komm_R.wav: Solo se deberían escuchar los instrumentos (derecha).")
    print("  - komm_semisuma.wav: Se escuchará toda la mezcla (mono perfecto).")
    print("  - komm_cod32.wav: Se escuchará en mono (en reproductores normales).")
    print("  - komm_dec32.wav: ¡Volverá a sonar en estéreo impecable!")
    print("==================================================")

if __name__ == "__main__":
    probar_practica()
