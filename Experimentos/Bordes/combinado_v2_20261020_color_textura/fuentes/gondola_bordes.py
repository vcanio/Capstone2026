import argparse
import json
import os

import cv2
import numpy as np

CARPETA_SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salidas")


# ---------- Lectura / escritura (funciona con rutas con acentos en Windows) ----------
def leer_imagen(ruta):
    try:
        datos = np.fromfile(ruta, dtype=np.uint8)
    except OSError:
        return None
    if datos.size == 0:
        return None
    try:
        return cv2.imdecode(datos, cv2.IMREAD_COLOR)
    except cv2.error:
        return None


def guardar_imagen(ruta, img):
    ok, buf = cv2.imencode(os.path.splitext(ruta)[1], img)
    if ok:
        buf.tofile(ruta)
    return ok


# ---------- Editor de cajas: todas se dibujan en la MISMA ventana ----------
def editor_rois(img, rois_iniciales=None, max_alto=900, max_ancho=1400):
    escala = min(1.0, max_alto / img.shape[0], max_ancho / img.shape[1])
    vista = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    alto_v, ancho_v = vista.shape[:2]
    rois = [list(r) for r in (rois_iniciales or [])]  # coordenadas de la imagen original
    estado = {"p0": None, "p1": None}
    ventana = "Editor de niveles"

    def texto(lienzo, s, pos, color, tam=0.6):
        cv2.putText(lienzo, s, pos, cv2.FONT_HERSHEY_SIMPLEX, tam, (0, 0, 0), 3)
        cv2.putText(lienzo, s, pos, cv2.FONT_HERSHEY_SIMPLEX, tam, color, 1)

    def redibujar():
        lienzo = vista.copy()
        for i, (x, y, w, h) in enumerate(rois):
            p0 = (int(x * escala), int(y * escala))
            p1 = (int((x + w) * escala), int((y + h) * escala))
            cv2.rectangle(lienzo, p0, p1, (0, 200, 0), 2)
            texto(lienzo, f"N{i + 1}", (p0[0] + 6, p0[1] + 22), (0, 255, 255), 0.7)
        if estado["p0"] is not None and estado["p1"] is not None:
            cv2.rectangle(lienzo, estado["p0"], estado["p1"], (0, 140, 255), 2)
        texto(lienzo, "Arrastra: nueva caja | U: deshacer | C: borrar todo | ENTER: terminar",
              (10, 22), (255, 255, 255))
        texto(lienzo, f"Cajas: {len(rois)}", (10, 46), (255, 255, 255))
        cv2.imshow(ventana, lienzo)

    def mouse(evento, x, y, flags, _):
        x = min(max(x, 0), ancho_v - 1)
        y = min(max(y, 0), alto_v - 1)
        if evento == cv2.EVENT_LBUTTONDOWN:
            estado["p0"] = (x, y)
            estado["p1"] = (x, y)
        elif evento == cv2.EVENT_MOUSEMOVE and estado["p0"] is not None:
            estado["p1"] = (x, y)
            redibujar()
        elif evento == cv2.EVENT_LBUTTONUP and estado["p0"] is not None:
            xa, xb = sorted((estado["p0"][0], x))
            ya, yb = sorted((estado["p0"][1], y))
            estado["p0"] = estado["p1"] = None
            if xb - xa >= 8 and yb - ya >= 8:
                rois.append([int(xa / escala), int(ya / escala),
                             int((xb - xa) / escala), int((yb - ya) / escala)])
            redibujar()

    cv2.namedWindow(ventana, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(ventana, mouse)
    redibujar()
    while True:
        tecla = cv2.waitKey(30) & 0xFF
        if tecla in (13, 32, ord("s")):          # ENTER, ESPACIO o S: terminar
            break
        if tecla in (ord("u"), ord("z"), 8) and rois:   # U, Z o Retroceso: deshacer
            rois.pop()
            redibujar()
        elif tecla == ord("c"):                  # C: borrar todo
            rois.clear()
            redibujar()
        elif tecla == 27:                        # ESC: cancelar
            cv2.destroyAllWindows()
            raise SystemExit("Cancelado.")
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyAllWindows()
    return rois


def obtener_rois(img, ruta_rois, reeditar):
    existentes = None
    if os.path.exists(ruta_rois):
        with open(ruta_rois) as f:
            existentes = json.load(f)
        if not reeditar:
            return existentes
    rois = editor_rois(img, existentes)
    if not rois:
        raise SystemExit("No se dibujo ninguna caja.")
    with open(ruta_rois, "w") as f:
        json.dump(rois, f)
    return rois


# ---------- Mapa de bordes ----------
def mapa_bordes(img, canny_lo, canny_hi):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gris = cv2.medianBlur(gris, 7)          # quita ruido sin borrar bordes reales
    gris = cv2.GaussianBlur(gris, (5, 5), 0)
    bordes = cv2.Canny(gris, canny_lo, canny_hi)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.morphologyEx(bordes, cv2.MORPH_CLOSE, kernel)


def quitar_lineas_largas(recorte, largo_min):
    """Borra rieles, postes y bordes de estante (lineas rectas largas, en cualquier angulo)."""
    limpio = recorte.copy()
    lineas = cv2.HoughLinesP(recorte, 1, np.pi / 180, threshold=50,
                             minLineLength=largo_min, maxLineGap=10)
    if lineas is not None:
        # OpenCV 4 devuelve (N,1,4) y OpenCV 5 puede devolver (N,4): se unifica la forma
        for x1, y1, x2, y2 in np.asarray(lineas).reshape(-1, 4):
            cv2.line(limpio, (int(x1), int(y1)), (int(x2), int(y2)), 0, 7)
    return limpio


# ---------- Ocupacion por caja ----------
def validar_parametros(a):
    if (a.cell < 2 or not 0 <= a.margin < .5 or a.open < 1 or
            not 0 <= a.canny[0] < a.canny[1] <= 255 or not 0 <= a.thr <= 1 or
            not 0 <= a.color_frac <= 1 or not 0 <= a.sat <= 255 or
            not 0 <= a.vmin <= 255 or a.tex < 0 or not 0 <= a.tex_vmax <= 255 or
            not 0 <= a.line <= 1):
        raise ValueError("Parametros de bordes, color, textura o grilla invalidos.")


def analizar(img, rois, a):
    validar_parametros(a)
    if img is None or img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("Se requiere una imagen BGR valida.")
    bordes = mapa_bordes(img, a.canny[0], a.canny[1])
    hsv = cv2.cvtColor(cv2.GaussianBlur(img, (5, 5), 0), cv2.COLOR_BGR2HSV)
    gris_t = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5).astype(np.float32)
    largo_min = max(30, int(a.line * img.shape[1]))
    vis_bordes = (bordes // 3).astype(np.uint8)        # gris: bordes descartados
    resultados = []
    for roi in rois:
        if len(roi) != 4 or not all(np.isfinite(value) for value in roi):
            raise ValueError("Cada caja requiere cuatro coordenadas finitas: x, y, ancho, alto.")
        x, y, w, h = (int(value) for value in roi)
        if w <= 0 or h <= 0:
            resultados.append({"pct": None, "zona": (0, 0, 0, 0), "grid": None,
                               "status": "sin_medicion", "reason": "Caja sin dimensiones positivas."})
            continue
        x1, y1 = min(img.shape[1], x+w), min(img.shape[0], y+h)
        x, y = max(0, x), max(0, y)
        w, h = max(0, x1-x), max(0, y1-y)
        # Zona realmente analizada: la caja menos un margen interior
        mx, my = int(w * a.margin), int(h * a.margin)
        x0, y0, w0, h0 = x + mx, y + my, w - 2 * mx, h - 2 * my
        if w0 < a.cell or h0 < a.cell:
            resultados.append({"pct": None, "zona": (x0, y0, w0, h0), "grid": None,
                               "status": "sin_medicion", "reason": "Caja fuera de la imagen o demasiado pequena."})
            continue

        recorte = quitar_lineas_largas(bordes[y0:y0 + h0, x0:x0 + w0], largo_min)
        vis_bordes[y0:y0 + h0, x0:x0 + w0] = recorte    # blanco: bordes contados

        # Criterio 1: densidad de bordes por celda (vectorizado)
        nw, nh = max(1, round(w0 / a.cell)), max(1, round(h0 / a.cell))
        densidad = cv2.resize(recorte.astype(np.float32) / 255.0, (nw, nh),
                              interpolation=cv2.INTER_AREA)
        grid = (densidad > a.thr).astype(np.uint8)

        # Criterio 2 (apoyo): color intenso, para productos lisos o de colores fuertes
        if a.color_frac > 0:
            hsv_r = hsv[y0:y0 + h0, x0:x0 + w0]
            # La saturacion de pixeles casi negros es ruido: solo se confia si hay brillo minimo
            intenso = ((hsv_r[..., 1] > a.sat) & (hsv_r[..., 2] > a.vmin)).astype(np.float32)
            dens_c = cv2.resize(intenso, (nw, nh), interpolation=cv2.INTER_AREA)
            grid = grid | (dens_c > a.color_frac).astype(np.uint8)

        # Criterio 3 (apoyo): textura en zonas oscuras o medias (botellas negras, envases oscuros).
        # Un panel negro liso casi no tiene variacion de brillo; un producto oscuro si (reflejos, relieve).
        if a.tex > 0:
            gz = gris_t[y0:y0 + h0, x0:x0 + w0]
            media = cv2.resize(gz, (nw, nh), interpolation=cv2.INTER_AREA)
            media2 = cv2.resize(gz * gz, (nw, nh), interpolation=cv2.INTER_AREA)
            desv = np.sqrt(np.maximum(media2 - media * media, 0))   # desviacion estandar por celda
            grid = grid | ((desv > a.tex) & (media < a.tex_vmax)).astype(np.uint8)

        # Limpieza sobre la grilla: quita celdas sueltas y lineas delgadas
        if a.open > 1:
            grid = cv2.morphologyEx(grid, cv2.MORPH_OPEN, np.ones((a.open, a.open), np.uint8))
            grid = cv2.morphologyEx(grid, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

        pct = 100.0 * grid.sum() / grid.size
        resultados.append({"pct": float(pct), "zona": (x0, y0, w0, h0), "grid": grid,
                           "status": "medido", "reason": None})
    return resultados, vis_bordes


def dibujar(img, resultados):
    salida = img.copy()
    capa = img.copy()
    for r in resultados:
        if r["grid"] is None:
            continue
        x0, y0, w0, h0 = r["zona"]
        mascara = cv2.resize(r["grid"], (w0, h0), interpolation=cv2.INTER_NEAREST) > 0
        capa[y0:y0 + h0, x0:x0 + w0][mascara] = (0, 0, 255)
    salida = cv2.addWeighted(capa, 0.35, salida, 0.65, 0)
    esc = max(img.shape[1] / 1800.0, 0.6)
    for i, r in enumerate(resultados):
        if r["grid"] is None:
            continue
        x0, y0, w0, h0 = r["zona"]
        cv2.rectangle(salida, (x0, y0), (x0 + w0, y0 + h0), (0, 200, 0), max(2, int(3 * esc)))
        txt = f"N{i + 1}: {r['pct']:.0f}%"
        pos = (x0 + 10, y0 + int(45 * esc))
        cv2.putText(salida, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.4 * esc, (0, 0, 0), int(6 * esc))
        cv2.putText(salida, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.4 * esc, (0, 255, 255), int(3 * esc))
    return salida


# ---------- Prueba de robustez (AlbumentationsX si esta instalado; si no, ruido propio) ----------
def crear_aumento():
    try:
        import albumentations as A
        t = A.Compose([
            A.GaussNoise(std_range=(0.03, 0.10), p=1.0),
            A.MotionBlur(blur_limit=(3, 7), p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
        ])
        return (lambda im: t(image=im)["image"]), "AlbumentationsX"
    except Exception:
        rng = np.random.default_rng(42)

        def basico(im):
            out = im.astype(np.float32)
            out += rng.normal(0, rng.uniform(5, 25), im.shape)
            out = out * rng.uniform(0.85, 1.15) + rng.uniform(-20, 20)
            out = np.clip(out, 0, 255).astype(np.uint8)
            if rng.random() < 0.5:
                k = int(rng.choice([3, 5, 7]))
                nucleo = np.zeros((k, k), np.float32)
                nucleo[k // 2, :] = 1.0 / k
                out = cv2.filter2D(out, -1, nucleo)
            return out

        return basico, "ruido propio (AlbumentationsX no disponible)"


def prueba_estres(img, rois, args, n):
    aumentar, origen = crear_aumento()
    print(f"\nPrueba de estres con {origen} ({n} iteraciones):")
    todos = []
    for _ in range(n):
        res, _ = analizar(aumentar(img), rois, args)
        todos.append([np.nan if r["pct"] is None else r["pct"] for r in res])
    todos = np.array(todos, dtype=float)
    for i in range(todos.shape[1]):
        if np.isnan(todos[:, i]).all():
            print(f"  N{i + 1}: sin medicion")
        else:
            print(f"  N{i + 1}: {np.nanmean(todos[:, i]):.1f}% +/- {np.nanstd(todos[:, i]):.1f}")


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Ocupacion de gondola por deteccion de bordes")
    ap.add_argument("imagen")
    ap.add_argument("--out", default=CARPETA_SALIDA, help="carpeta donde se guardan los resultados")
    ap.add_argument("--rois", help="ruta del JSON de cajas (por defecto <out>/<imagen>_rois.json)")
    ap.add_argument("--reselect", action="store_true",
                    help="abrir el editor de nuevo (conserva las cajas existentes)")
    ap.add_argument("--canny", type=int, nargs=2, default=[40, 120], metavar=("LO", "HI"))
    ap.add_argument("--cell", type=int, default=24, help="tamano de celda en px")
    ap.add_argument("--thr", type=float, default=0.04, help="densidad minima de bordes por celda")
    ap.add_argument("--margin", type=float, default=0.03,
                    help="margen interior ignorado en cada caja (0.03 = 3%%)")
    ap.add_argument("--open", type=int, default=3,
                    help="bloque minimo en celdas para contar como ocupado (1 = sin filtro)")
    ap.add_argument("--line", type=float, default=0.04,
                    help="largo minimo (fraccion del ancho de la foto) de las lineas rectas que se descartan")
    ap.add_argument("--color-frac", dest="color_frac", type=float, default=0.35,
                    help="fraccion minima de color con brillo suficiente (0 = desactiva color)")
    ap.add_argument("--sat", type=int, default=70, help="saturacion minima (0-255) para considerar color")
    ap.add_argument("--vmin", type=int, default=50,
                    help="brillo minimo (0-255) para confiar en la saturacion del color")
    ap.add_argument("--tex", type=float, default=4.0,
                    help="desviacion estandar minima del brillo en una celda oscura para contarla (0 = no usar)")
    ap.add_argument("--tex-vmax", dest="tex_vmax", type=int, default=90,
                    help="brillo medio maximo (0-255) de la celda para aplicar el criterio de textura")
    # Opciones de la version anterior: se aceptan para no romper comandos, pero ya no tienen efecto
    ap.add_argument("--dark", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--dark-radio", dest="dark_radio", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--dark-bloque", dest="dark_bloque", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--stress", type=int, default=0, help="iteraciones con ruido")
    ap.add_argument("--levels", type=int, help=argparse.SUPPRESS)  # ya no se usa
    args = ap.parse_args()
    try:
        validar_parametros(args)
    except ValueError as error:
        ap.error(str(error))

    img = leer_imagen(args.imagen)
    if img is None:
        raise SystemExit(f"No se pudo leer {args.imagen}")

    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.imagen))[0]
    ruta_rois = args.rois or os.path.join(args.out, f"{base}_rois.json")
    rois = obtener_rois(img, ruta_rois, args.reselect)

    resultados, vis_bordes = analizar(img, rois, args)

    print()
    for i, r in enumerate(resultados):
        if r['pct'] is None:
            print(f"N{i + 1}: sin medicion ({r['reason']})")
        else:
            print(f"N{i + 1}: area con senal {r['pct']:.1f}% (experimental)")

    ruta_b = os.path.join(args.out, f"{base}_bordes.png")
    ruta_r = os.path.join(args.out, f"{base}_resultado.png")
    guardar_imagen(ruta_b, vis_bordes)
    guardar_imagen(ruta_r, dibujar(img, resultados))
    ruta_datos = os.path.join(args.out, f"{base}_mediciones.json")
    with open(ruta_datos, "w", encoding="utf-8") as f:
        json.dump({"imagen": os.path.abspath(args.imagen), "parametros": vars(args),
                   "rois": rois, "resultados": [{**r, "grid": r["grid"].tolist() if r["grid"] is not None else None}
                                                   for r in resultados], "calibrado": False}, f,
                  ensure_ascii=False, indent=2, allow_nan=False)
    print(f"\nGuardado en {args.out}:\n  {base}_resultado.png\n  {base}_bordes.png")
    print(f"Cajas en: {ruta_rois}")

    if args.stress > 0:
        prueba_estres(img, rois, args, args.stress)


if __name__ == "__main__":
    main()
