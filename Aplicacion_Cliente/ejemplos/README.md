# Casos de ejemplo precargados en la app cliente

Este catálogo permite probar con un clic (**Probar un pasillo de ejemplo**) los distintos escenarios que maneja la aplicación cliente sin recurrir a la partición reservada `test` (`Ohiggins 3`).

## Casos incluidos

| Archivo | Caso demostrado | Origen | Fuente | SHA-256 |
|---|---|---|---|---|
| `01_sin_alertas.jpg` | Sin alertas (`suficiente`, 6 niveles) | Real (`train`, redimensionada) | `lider_express_014_0_original.jpg` | `bc19b6506f6b6345b091265dc259addff1c5045f086161ae379599da53e4d98f` |
| `02_alertas_critica_alta.jpg` | Alertas `critica` y `alta` + vista Huecos | Variante sintética (`train`, redimensionada) | `lider_express_014_C_mixta.png` | `551ecf791199b35067fc2e4116454d40ee9822dbdb354c1baf987bcb2fd7628a` |
| `03_requiere_revision_borde.jpg` | Nivel en el borde (`near_frame`, revisión) | Variante sintética (fuera de `test`, redimensionada) | `lider_express_010_D_persona.png` | `f6703a10d5310002f43a4217fa28342f7f50f9fb51495c77ff14af50b3a3eb0b` |
| `04_persona_obstruyendo.jpg` | Foto `no_evaluable` por persona (`oclusiones.py`) | Variante sintética (fuera de `test`, redimensionada) | `lider_express_002_D_persona.png` | `c4a85abac23718a0f7f2de58170a1a9db5659c606d9545bf0fa26804bf06ad89` |
| `05_foto_oscura.jpg` | Foto `no_evaluable` (`subexpuesta`) | Generada por script | Imagen sintética oscura | `733f31cf18b0b9b3a1f3ec1110663f8fd7c31e8327df56d6190adab900ebba0d` |
| `06_foto_sobreexpuesta.jpg` | Foto `no_evaluable` (`sobreexpuesta`) | Generada por script | Imagen sintética sobreexpuesta | `325e955907dd757072077891de69f809a9fe3c232db2f494de8ecb552eed24e3` |
| `07_foto_borrosa.jpg` | Foto `no_evaluable` (`desenfoque`) | Generada (`GaussianBlur`) | Derivada de `01_sin_alertas.jpg` | `76ea4c0c243a28af828ba041239e9cb3bd130d18dc6e6ce54e4b656d5445f54c` |
| `08_sin_niveles.jpg` | Sin niveles detectados (`verificar`) | Generada por script | Ruido sin góndolas | `b9a6b0589aecf4d25249856c05bb180321be733cf5604380e2a901f6ea9b1487` |

## Alcance y licencias

- Ninguna imagen pertenece a la partición reservada `test` (`Ohiggins 3`).
- Las variantes sintéticas y capturas incluidas fueron autorizadas por Vicente (17/11/2026) exclusivamente como demostración funcional dentro de la app cliente; no otorgan licencia abierta al resto del dataset ni sustituyen una evaluación de precisión. Consulta [LICENCIAS.md](../../LICENCIAS.md).
