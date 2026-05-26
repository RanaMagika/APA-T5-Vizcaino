from estereo import estereo2mono, mono2estereo, codEstereo, decEstereo

# 1. Probar reducción a mono (canal semisuma)
estereo2mono("komm.wav", "komm_mono.wav", canal=2)

# 2. Probar codificación y decodificación en 32 bits
codEstereo("komm.wav", "komm_codificado.wav")
decEstereo("komm_codificado.wav", "komm_decodificado.wav")

