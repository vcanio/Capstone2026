import argparse
import json
import os

import cv2
import numpy as np

CARPETA_SALIDA = r"E:\openCV\fotos"


# ---------- Lectura / escritura (funciona con rutas con acentos en Windows) ----------
def leer_imagen(ruta):
    try:
        datos = np.fromfile(ruta, dtype=np.uint8)
    except OSError:
        return None
    return cv2.imdecode(datos, cv2.IMREAD_COLOR)


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


# ---------- Ocupacion por caja: criterio clasico adaptativo, sin entrenamiento ----------
def normalizar_por_roi(mapa, p_bajo=10, p_alto=90):
    """Escala un mapa de caracteristicas segun sus percentiles dentro del nivel."""
    mapa = mapa.astype(np.float32)
    bajo, alto = np.percentile(mapa, [p_bajo, p_alto])
    if alto - bajo < 1e-6:
        return np.zeros_like(mapa, dtype=np.float32)
    return np.clip((mapa - bajo) / (alto - bajo), 0.0, 1.0)


def umbral_adaptativo(scores):
    """Usa Otsu sobre la puntuacion de celdas, con un minimo conservador."""
    s8 = np.clip(scores * 255.0, 0, 255).astype(np.uint8)
    if s8.size < 2 or int(s8.max()) == int(s8.min()):
        return 0.42
    otsu, _ = cv2.threshold(s8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Evita que Otsu use un umbral casi cero cuando hay mucho ruido de fondo.
    return float(np.clip(otsu / 255.0, 0.35, 0.62))


def analizar(img, rois, a):
    bordes = mapa_bordes(img, a.canny[0], a.canny[1])
    img_suave = cv2.GaussianBlur(img, (5, 5), 0)
    hsv = cv2.cvtColor(img_suave, cv2.COLOR_BGR2HSV)
    gris = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5).astype(np.float32)
    # Magnitud del gradiente: detecta cambios locales incluso en productos poco saturados.
    gx = cv2.Sobel(gris, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gris, cv2.CV_32F, 0, 1, ksize=3)
    gradiente = cv2.magnitude(gx, gy)
    largo_min = max(30, int(a.line * img.shape[1]))
    vis_bordes = (bordes // 3).astype(np.uint8)
    resultados = []

    for (x, y, w, h) in rois:
        mx, my = int(w * a.margin), int(h * a.margin)
        x0, y0, w0, h0 = x + mx, y + my, w - 2 * mx, h - 2 * my
        if w0 < a.cell or h0 < a.cell:
            resultados.append({"pct": 0.0, "zona": (x0, y0, w0, h0), "grid": None})
            continue

        recorte_bordes = quitar_lineas_largas(bordes[y0:y0+h0, x0:x0+w0], largo_min)
        vis_bordes[y0:y0+h0, x0:x0+w0] = recorte_bordes
        nw = max(1, round(w0 / a.cell))
        nh = max(1, round(h0 / a.cell))

        # Calcula caracteristicas por celda. Cada una aporta una señal distinta;
        # no se marca ocupada solo porque se cumpla cualquiera de varios umbrales fijos.
        dens_bordes = cv2.resize(recorte_bordes.astype(np.float32) / 255.0,
                                 (nw, nh), interpolation=cv2.INTER_AREA)
        hsv_r = hsv[y0:y0+h0, x0:x0+w0]
        pix_color = ((hsv_r[..., 1] > a.sat) & (hsv_r[..., 2] > a.vmin)).astype(np.float32)
        fraccion_color = cv2.resize(pix_color, (nw, nh), interpolation=cv2.INTER_AREA)

        g = gris[y0:y0+h0, x0:x0+w0]
        media = cv2.resize(g, (nw, nh), interpolation=cv2.INTER_AREA)
        media2 = cv2.resize(g*g, (nw, nh), interpolation=cv2.INTER_AREA)
        textura = np.sqrt(np.maximum(media2 - media*media, 0.0))
        grad_r = gradiente[y0:y0+h0, x0:x0+w0]
        grad_celda = cv2.resize(grad_r, (nw, nh), interpolation=cv2.INTER_AREA)

        # Normalizacion relativa a cada nivel: tolera mejor cambios de luz y contraste.
        b = normalizar_por_roi(dens_bordes)
        gnorm = normalizar_por_roi(grad_celda)
        c = normalizar_por_roi(fraccion_color)
        t = normalizar_por_roi(textura)

        # Bordes y gradientes tienen mayor peso; color y textura son apoyos.
        score = 0.35*b + 0.30*gnorm + 0.20*c + 0.15*t
        umbral = umbral_adaptativo(score)
        grid = (score >= umbral).astype(np.uint8)

        # Cierre para unir huecos pequeños dentro de zonas de producto.
        # La apertura se deja opcional porque puede borrar productos delgados.
        if a.open > 1:
            k = np.ones((a.open, a.open), np.uint8)
            grid = cv2.morphologyEx(grid, cv2.MORPH_OPEN, k)
        grid = cv2.morphologyEx(grid, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

        pct = 100.0 * float(grid.mean())
        resultados.append({"pct": pct, "zona": (x0, y0, w0, h0), "grid": grid})
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
        todos.append([r["pct"] for r in res])
    todos = np.array(todos)
    for i in range(todos.shape[1]):
        print(f"  N{i + 1}: {todos[:, i].mean():.1f}% +/- {todos[:, i].std():.1f}")


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Ocupacion de gondola por criterios clasicos adaptativos (sin entrenamiento)")
    ap.add_argument("imagen")
    ap.add_argument("--out", default=CARPETA_SALIDA, help="carpeta donde se guardan los resultados")
    ap.add_argument("--rois", help="ruta del JSON de cajas (por defecto <out>/<imagen>_rois.json)")
    ap.add_argument("--reselect", action="store_true",
                    help="abrir el editor de nuevo (conserva las cajas existentes)")
    ap.add_argument("--canny", type=int, nargs=2, default=[40, 120], metavar=("LO", "HI"))
    ap.add_argument("--cell", type=int, default=24, help="tamano de celda en px")
    ap.add_argument("--thr", type=float, default=0.04, help="conservado por compatibilidad; el umbral ahora se adapta por nivel")
    ap.add_argument("--margin", type=float, default=0.03,
                    help="margen interior ignorado en cada caja (0.03 = 3%%)")
    ap.add_argument("--open", type=int, default=1,
                    help="apertura morfologica opcional en celdas (1 = desactivada)")
    ap.add_argument("--line", type=float, default=0.04,
                    help="largo minimo (fraccion del ancho de la foto) de las lineas rectas que se descartan")
    ap.add_argument("--color-frac", dest="color_frac", type=float, default=0.35,
                    help="conservado por compatibilidad; el color aporta una puntuacion relativa")
    ap.add_argument("--sat", type=int, default=70, help="saturacion minima (0-255) para considerar color")
    ap.add_argument("--vmin", type=int, default=50,
                    help="brillo minimo (0-255) para confiar en la saturacion del color")
    ap.add_argument("--tex", type=float, default=4.0,
                    help="conservado por compatibilidad; la textura aporta una puntuacion relativa")
    ap.add_argument("--tex-vmax", dest="tex_vmax", type=int, default=90,
                    help="brillo medio maximo (0-255) de la celda para aplicar el criterio de textura")
    # Opciones de la version anterior: se aceptan para no romper comandos, pero ya no tienen efecto
    ap.add_argument("--dark", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--dark-radio", dest="dark_radio", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--dark-bloque", dest="dark_bloque", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--stress", type=int, default=0, help="iteraciones con ruido")
    ap.add_argument("--levels", type=int, help=argparse.SUPPRESS)  # ya no se usa
    args = ap.parse_args()

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
        print(f"N{i + 1}: ocupado {r['pct']:.1f}%  |  vacio {100 - r['pct']:.1f}%")

    ruta_b = os.path.join(args.out, f"{base}_bordes.png")
    ruta_r = os.path.join(args.out, f"{base}_resultado.png")
    guardar_imagen(ruta_b, vis_bordes)
    guardar_imagen(ruta_r, dibujar(img, resultados))
    print(f"\nGuardado en {args.out}:\n  {base}_resultado.png\n  {base}_bordes.png")
    print(f"Cajas en: {ruta_rois}")

    if args.stress > 0:
        prueba_estres(img, rois, args, args.stress)


if __name__ == "__main__":
    main()
