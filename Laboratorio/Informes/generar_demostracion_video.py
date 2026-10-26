"""Monta la demostración del 21 de octubre desde voz y capturas locales verificadas.

Los insumos privados se conservan en .tmp/demo_nueva_20261021. No ejecuta modelos,
no fabrica resultados y no publica el video. Requiere Pillow e imageio-ffmpeg.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import unicodedata

from PIL import Image, ImageDraw, ImageFont, ImageOps
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '.tmp/demo_nueva_20261021'
W, H, FPS, INTRO, OUTRO = 1920, 1080, 25, 3.0, 8.0
FF = imageio_ffmpeg.get_ffmpeg_exe()
NAVY, BLUE, GOLD, INK = '#102d4e', '#0061bd', '#ffc220', '#172b40'


def run(args):
    p = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)],
                       cwd=BASE, capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace')[-5000:])


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('segoeuib.ttf' if bold else 'segoeui.ttf'), size)


def wrap(draw, text, size, width, bold=False):
    lines, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if line and draw.textlength(candidate, font=font(size, bold)) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + ([line] if line else [])


def text(draw, xy, message, size=32, width=500, fill=INK, bold=False, leading=1.32):
    x, y = xy
    for line in wrap(draw, message, size, width, bold):
        draw.text((x, y), line, font=font(size, bold), fill=fill)
        y += round(size * leading)
    return y


def norm(word):
    word = ''.join(c for c in unicodedata.normalize('NFD', word.lower()) if not unicodedata.combining(c))
    word = re.sub(r'[^a-z0-9]', '', word)
    return {'jolo': 'yolo', 'dos': '2', 'uno': '1', 'veinte': '20'}.get(word, word)


def stamp(value, ass=False):
    value = round(value * (100 if ass else 1000))
    unit = 100 if ass else 1000
    hours, value = divmod(value, unit * 3600)
    minutes, value = divmod(value, unit * 60)
    seconds, frac = divmod(value, unit)
    return f'{hours}:{minutes:02}:{seconds:02}.{frac:02}' if ass else f'{hours:02}:{minutes:02}:{seconds:02},{frac:03}'


def prepare_audio():
    raw = json.loads((BASE / 'audio/transcripcion.json').read_text(encoding='utf-8'))
    asr = [w for segment in raw for w in segment['words'] if norm(w['word'])]
    # El reconocimiento a veces escribe la marca YOLO como dos palabras.
    joined = []
    i = 0
    while i < len(asr):
        w = dict(asr[i])
        if i + 1 < len(asr) and norm(w['word']) == 'yo' and norm(asr[i + 1]['word']) == 'lo':
            w.update(word='YOLO', end=asr[i + 1]['end'])
            i += 1
        if i + 1 < len(asr) and norm(w['word']) == 'yolo' and norm(asr[i + 1]['word']) == '26':
            w.update(word='YOLO26', end=asr[i + 1]['end'])
            i += 1
        joined.append(w)
        i += 1
    source = (ROOT / 'Documentacion/Demostracion/Guion_locucion_20261021.md').read_text(encoding='utf-8')
    blocks = re.split(r'^## ', source, flags=re.M)[1:]
    canonical, block_indices = [], []
    for block in blocks:
        title, body = block.split('\n', 1)
        block_indices.append((len(canonical), title))
        canonical.extend(body.split())
    matcher = difflib.SequenceMatcher(None, [norm(w) for w in canonical], [norm(w['word']) for w in joined], autojunk=False)
    aligned = [None] * len(canonical)
    equal = 0
    changes = []
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag == 'equal':
            equal += b - a
            for j, k in zip(range(a, b), range(c, d)):
                aligned[j] = dict(text=canonical[j], start=joined[k]['start'], end=joined[k]['end'])
        elif b > a:
            start = joined[c]['start'] if c < len(joined) else joined[-1]['end']
            end = joined[d - 1]['end'] if d > c else start + 0.08 * (b - a)
            end = max(end, start + 0.04 * (b - a))
            for j in range(a, b):
                aligned[j] = dict(text=canonical[j], start=start + (end-start)*(j-a)/(b-a),
                                  end=start + (end-start)*(j-a+1)/(b-a))
            changes.append(dict(guion=' '.join(canonical[a:b]), reconocimiento=' '.join(w['word'] for w in joined[c:d]), start=start, end=end))
    if equal / len(canonical) < 0.90:
        raise ValueError('La voz difiere demasiado del guion: revisar antes de subtitular.')
    cues, group = [], []
    for word in aligned:
        candidate = ' '.join(w['text'] for w in [*group, word])
        if group and (len(candidate) > 82 or word['end'] - group[0]['start'] > 6.0):
            cues.append(group)
            group = []
        group.append(word)
        if re.search(r'[.!?]$', word['text']) and len(' '.join(w['text'] for w in group)) > 28:
            cues.append(group)
            group = []
    if group:
        cues.append(group)
    subtitles = []
    for group in cues:
        subtitles.append(dict(start=round(group[0]['start']+INTRO, 3), end=round(group[-1]['end']+INTRO, 3),
                              text=' '.join(w['text'] for w in group)))
    # Evitar solapamientos producidos por marcas de palabras compartidas.
    for i in range(len(subtitles)-1):
        subtitles[i]['end'] = min(subtitles[i]['end'], subtitles[i+1]['start'])
    out = ROOT / 'Documentacion/Demostracion/Subtitulos_Demostracion_20261021.srt'
    out.write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(subtitles))+'\n',encoding='utf-8')
    ass_header = '[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Segoe UI,36,&H00FFFFFF,&H00FFFFFF,&H00101C2C,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,140,140,25,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    ass_lines = []
    dummy = ImageDraw.Draw(Image.new('RGB',(W,H)))
    for cue in subtitles:
        label = r'\N'.join(wrap(dummy, cue['text'], 36, 1600))
        ass_lines.append(f"Dialogue: 0,{stamp(cue['start'],True)},{stamp(cue['end'],True)},Default,,0,0,0,,{label}")
    (BASE/'subtitulos.ass').write_text(ass_header+'\n'.join(ass_lines)+'\n',encoding='utf-8')
    block_times = [dict(title=title,start=round(aligned[index]['start'],3)) for index,title in block_indices]
    alignment = dict(equal_token_ratio=equal/len(canonical),script_words=len(canonical),recognized_words=len(joined),changes=changes,blocks=block_times,cues=len(cues))
    (BASE/'audio/alineacion.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2),encoding='utf-8')
    return alignment


def shell(title, tag='DEMOSTRACIÓN FUNCIONAL'):
    canvas = Image.new('RGB',(W,H),'#f1f5fa')
    d = ImageDraw.Draw(canvas)
    d.rectangle((0,0,W,108),fill=NAVY)
    d.text((55,24),'Walmart Visión',font=font(39,True),fill='white')
    box = d.textbbox((0,0),tag,font=font(23,True))
    d.text((W-58-box[2],39),tag,font=font(23,True),fill=GOLD)
    d.text((55,129),title,font=font(42,True),fill=INK)
    d.rectangle((0,949,W,H),fill='#101c2c')
    d.rectangle((55,929,1865,932),fill='#d7e2ef')
    return canvas,d


def place(canvas, source, box, crop=None):
    if isinstance(source, (str,Path)):
        source = Image.open(source).convert('RGB')
    if crop:
        source = source.crop(crop)
    x,y,right,bottom = box
    picture = ImageOps.contain(source,(right-x,bottom-y),Image.Resampling.LANCZOS)
    canvas.paste(picture,(x+(right-x-picture.width)//2,y+(bottom-y-picture.height)//2))


def note(d, title, points):
    d.rounded_rectangle((1425,225,1865,897),radius=16,fill=NAVY)
    y=text(d,(1455,253),title,31,380,'white',True)
    y+=30
    for item in points:
        d.ellipse((1457,y+12,1465,y+20),fill=GOLD)
        y=text(d,(1486,y),item,27,345,'#e4edf8')+28


def app(title, name, points=(), crop=None, tag='EJECUCIÓN LOCAL · 21 OCT 2026'):
    im,d=shell(title,tag)
    source=BASE/'capturas'/name
    if points:
        place(im,source,(55,213,1396,913),crop)
        note(d,'Qué revisar',points)
    else:
        place(im,source,(55,213,1865,913),crop)
    return im


def graphic(title, cards, footer=None):
    im,d=shell(title)
    cols=len(cards)
    width=(1810-30*(cols-1))//cols
    for i,(heading,body) in enumerate(cards):
        x=55+i*(width+30)
        d.rounded_rectangle((x,260,x+width,800),radius=18,fill='white',outline='#d5e1ee',width=2)
        d.rectangle((x,260,x+width,270),fill=BLUE if i%2==0 else GOLD)
        y=text(d,(x+30,310),heading,37,width-60,INK,True)
        text(d,(x+30,y+32),body,31,width-60,'#445c75')
    if footer:
        text(d,(65,842),footer,28,1775,BLUE,True)
    return im


def controls():
    im,d=shell('Elegir modelo, método y confianza','EJECUCIÓN LOCAL · CONTROLES AMPLIADOS')
    for x,label,crop in [(55,'Modelo y método',(110,325,385,575)),
                         (1000,'Confianza mínima',(110,720,385,899))]:
        d.rounded_rectangle((x,220,x+865,900),radius=14,fill='white')
        d.text((x+25,242),label,font=font(31,True),fill=INK)
        place(im,BASE/'capturas/04_ajustes.jpg',(x+25,315,x+840,870),crop)
    return im


def case(case_id,title,types=('original','yolo','bordes'),crop=None,footer=''):
    im,d=shell(title,'EVIDENCIA DEL INFORME · '+case_id)
    labels={'original':'Entrada original','yolo':'Resultado YOLO','bordes':'Mapa de señal'}
    gap=30
    width=(1810-gap*(len(types)-1))//len(types)
    for i,t in enumerate(types):
        x=55+i*(width+gap)
        d.rounded_rectangle((x,211,x+width,858),radius=12,fill='white')
        d.text((x+22,226),labels[t]+(' · detalle' if crop else ''),font=font(28,True),fill=INK)
        source=ROOT/'Documentacion/Evidencias/casos_yolo_bordes_20261021'/f'{case_id}_{t}.jpg'
        image=Image.open(source).convert('RGB')
        pixel_crop=None if crop is None else tuple(round(v*s) for v,s in zip(crop,(image.width,image.height,image.width,image.height)))
        place(im,image,(x+12,278,x+width-12,843),pixel_crop)
    text(d,(65,878),footer or 'Revisión visual de un caso seleccionado; no es una métrica global.',25,1780,'#415a73')
    return im


def build_scenes(duration):
    # Tiempos de la locución recibida, contrastados con las palabras reconocidas.
    scenes=[]
    def add(a,b,im,live=None):
        scenes.append(dict(start=a,end=b,image=im,live=live))
    add(0,INTRO,graphic('Una foto, nivel por nivel',[
        ('Disponibilidad visible','Identificar repisas y apoyar la revisión de posibles faltantes.'),
        ('Demostración funcional','Recorrido de la aplicación y cuatro casos del informe.')], 'YOLO + detección de bordes · prototipo académico'))
    add(INTRO,18.8,app('Apoyar la revisión de las góndolas','01_inicio.jpg',[
        'Fotografía como entrada','Disponibilidad visual por repisa','Revisión por una persona']))
    add(18.8,36.5,graphic('Qué veremos en esta demostración',[
        ('Usar la aplicación','Cargar una foto, analizarla y revisar los niveles encontrados.'),
        ('Entender los resultados','Dos casos favorables y dos con dificultades.')]))
    add(36.5,59.3,graphic('Cómo se obtiene el resultado',[
        ('1 · YOLO','Localiza los niveles y predice su estado.'),
        ('2 · Bordes','Estudia bordes, color y textura dentro de esas regiones.'),
        ('3 · Revisión','Contrastar la predicción con lo que se ve en la foto.')], 'La señal adicional no cambia el estado de YOLO.'))
    add(59.3,71.8,app('V2 · Reponer y suficiente','13_version_dos.jpg',[
        'Vacío y baja disponibilidad se agrupan en reponer','Modelo elegido: V2-YOLO26'],crop=(100,0,400,126)))
    add(71.8,78.32,app('También se puede seleccionar V1','12_version_uno.jpg',[
        'V1 tiene cuatro estados','V2 base todavía no reconoce no evaluable'],crop=(100,0,400,126)))
    add(78.32,87.1,app('Cargar una fotografía','02_foto_lista.jpg',['Foto de vinos','Entrada conocida de desarrollo','Modelo V2-YOLO26']))
    add(87.1,94.14,controls())
    live=json.loads((BASE/'secuencia/flujo_timeline.json').read_text(encoding='utf-8'))
    live_length=live[-1]['time']-live[0]['time']
    add(94.14,94.14+live_length,app('Analizar foto · secuencia de la ejecución','04_ajustes.jpg',[
        'Capturas consecutivas temporizadas','5 niveles encontrados','2 reponer y 3 suficientes']),live='flujo')
    add(94.14+live_length,110.92,app('Leer el detalle por nivel','05_detalle.jpg',[
        'Estado detectado','Confianza del modelo','Confianza no es ocupación'],crop=(425,1070,1480,1485)))
    add(110.92,119.92,app('Comparar la entrada y la predicción','06_comparar.jpg',[
        'Original a la izquierda','Predicción a la derecha','Revisar contornos y estados']))
    add(119.92,137.52,case('B06','Caso favorable · Vinos con faltantes',footer='Dos repisas casi vacías: la alerta y la evidencia visual coinciden.'))
    add(137.52,154.16,case('B06','B06 · Menos señal en las repisas con faltantes',('yolo','bordes'),footer='El mapa ayuda a revisar la escena; no mide inventario.'))
    add(154.16,163.38,graphic('Qué respalda este caso favorable',[
        ('Coherencia visual','Ubicación de los niveles, estado y señal concuerdan en este ejemplo.'),
        ('Validación pendiente','Medir el rendimiento general exige imágenes y referencias revisadas.')]))
    add(163.38,169.98,app('Activar YOLO + detección de bordes','07_metodo_bordes.jpg',[
        'Cambiar método','Volver a analizar','Abrir la pestaña Bordes']))
    add(169.98,175.46,app('Mapa de señal dentro de los niveles','15_mapa_completo.jpg',[
        'Amarillo: señal activada','Vista experimental'],crop=(420,230,1480,1250)))
    add(175.46,181.5,app('Bordes dentro de los niveles','16_bordes_completos.jpg',[
        'Contornos limitados a las regiones de YOLO','Vista de revisión experimental'],crop=(420,230,1480,1240)))
    add(181.5,191.56,app('Consultar las mediciones de señal','11_mediciones.jpg',[
        'Área con señal','Ancho con señal','No equivalen a producto real'],crop=(425,1575,1480,1970)))
    add(191.56,205.16,app('Señal experimental, no ocupación real','15_mapa_completo.jpg',[
        'Amarillo: señal activada','YOLO conserva su estado','Una señal baja no demuestra vacío'],crop=(420,230,1480,1250)))
    add(205.16,220.72,case('B08','Caso favorable · Bebidas en exhibidor',footer='Cuatro repisas separadas y señal concentrada principalmente en las botellas.'))
    add(220.72,242.04,case('B08','B08 · Separar el mueble del pasillo',('original','yolo'),footer='Se evalúa disponibilidad visual por nivel; no se cuentan botellas.'))
    add(242.04,260.98,case('F01','Dificultad · Señal sobre un fondo vacío',footer='El fondo metálico también activa parte de la señal experimental.'))
    add(260.98,275.2,case('F01','F01 · Revisar las activaciones del fondo',('original','bordes'),crop=(0.04,0.2,0.99,0.70),footer='Detalle ampliado: la señal no confirma presencia de productos.'))
    add(275.2,284.26,graphic('Mejora propuesta · Rechazo del fondo',[
        ('Comparar','Repisas vacías y ocupadas, con referencias revisadas.'),
        ('Comprobar','Reducir falsas activaciones sin perder productos oscuros.')]))
    add(284.26,297.9,case('F03','Dificultad · Una repisa sin contorno',footer='La fotografía muestra cuatro niveles físicos; la salida documentada dibuja tres.'))
    add(297.9,315.74,case('F03','F03 · Bordes depende de las regiones de YOLO',('original','yolo'),crop=(0,0.06,1,0.7),footer='Una repisa no delimitada queda fuera del análisis adicional.'))
    add(315.74,325.4,graphic('Mejora propuesta · Revisar la localización',[
        ('Comprobar la referencia','Revisar el nivel y repetir el análisis con el registro original.'),
        ('Verificar la causa','Sombra y similitud entre filas son hipótesis, todavía no causas demostradas.')]))
    add(325.4,344.92,graphic('Avances implementados',[
        ('Flujo operativo','Carga de fotos, versiones y modelos, predicción y detalle por nivel.'),
        ('Revisión visual','Comparación, vistas de bordes y veinte casos documentados.')]))
    add(344.92,371.54,graphic('Prioridades para mejorar los resultados',[
        ('Faltantes reales','Ampliar los ejemplos de reposición.'),
        ('Contornos y oclusiones','Revisar etiquetas y niveles omitidos.'),
        ('Señal y evaluación','Contrastar con referencias y conservar la prueba final.')], 'La selección de casos no estima una precisión global nueva.'))
    add(371.54,394.06,app('Probar Walmart Visión desde GitHub','14_release.jpg',[
        'Descargar el ZIP de la aplicación','Incluye interfaz y cuatro modelos','Guías para Windows y Docker'],crop=(0,110,1265,990),tag='DESCARGA DE LA APLICACIÓN'))
    add(394.06,413.59,graphic('Documentación y evidencias del proyecto',[
        ('Consultar','Informe, casos, guion y verificación de la demostración.'),
        ('Continuar','Mejorar las dificultades observadas y comprobar los resultados.')], 'github.com/vcanio/Capstone2026'))
    add(413.59,duration,graphic('Walmart Visión · Disponibilidad visual por nivel',[
        ('Probar la aplicación','Descarga disponible en Releases.'),
        ('Revisar el proyecto','Informe, documentación y evidencias en el repositorio.')], 'github.com/vcanio/Capstone2026'))
    for i,scene in enumerate(scenes):
        if scene['end'] <= scene['start']:
            raise ValueError(f'Escena de duración incorrecta: {i}')
        if i and abs(scene['start']-scenes[i-1]['end'])>0.002:
            raise ValueError(f'Hueco entre escenas: {i}')
    return scenes


def render(preview_only=False):
    BASE.mkdir(exist_ok=True)
    alignment=prepare_audio()
    # Decodificar para medir la duración real, sin confiar solo en la cabecera MP3.
    p=subprocess.run([FF,'-v','error','-i',str(BASE/'audio/AudioWalmart.mp3'),'-f','s16le','-ar','16000','-ac','1','-'],capture_output=True,check=True)
    audio_duration=len(p.stdout)/32000
    duration=INTRO+audio_duration+OUTRO
    scenes=build_scenes(duration)
    frames=BASE/'frames'
    clips=BASE/'clips'
    frames.mkdir(exist_ok=True)
    clips.mkdir(exist_ok=True)
    (BASE/'fonts').mkdir(exist_ok=True)
    shutil.copy2('C:/Windows/Fonts/segoeui.ttf',BASE/'fonts/segoeui.ttf')
    for i,scene in enumerate(scenes):
        scene['image'].save(frames/f'{i:02}.png')
    timeline=[dict(index=i,start=s['start'],end=s['end'],live=s['live']) for i,s in enumerate(scenes)]
    (BASE/'timeline.json').write_text(json.dumps(dict(audio_duration=audio_duration,duration=duration,scenes=timeline),indent=2),encoding='utf-8')
    if preview_only:
        print(json.dumps(dict(audio_duration=audio_duration,duration=duration,scenes=len(scenes),alignment=alignment['equal_token_ratio']),indent=2))
        return
    for i,scene in enumerate(scenes):
        output=clips/f'{i:02}.mp4'
        if output.exists():
            continue
        visual=['-loop','1','-framerate',str(FPS),'-i',frames/f'{i:02}.png']
        if scene['live']:
            source=json.loads((BASE/'secuencia/flujo_timeline.json').read_text(encoding='utf-8'))
            records=[]
            for k,entry in enumerate(source):
                canvas=scene['image'].copy()
                place(canvas,BASE/'secuencia'/entry['file'],(55,213,1396,913))
                path=frames/f'live_{k:03}.png'
                canvas.save(path)
                elapsed=source[k+1]['time']-entry['time'] if k+1<len(source) else 0.04
                records.extend([f"file 'frames/{path.name}'",f'duration {elapsed:.6f}'])
            records.append(f"file 'frames/live_{len(source)-1:03}.png'")
            (BASE/'live.txt').write_text('\n'.join(records),encoding='utf-8')
            visual=['-f','concat','-safe','0','-i',BASE/'live.txt']
        vf=f"setpts=PTS+{scene['start']}/TB,ass=subtitulos.ass:fontsdir=fonts,setpts=PTS-STARTPTS"
        run([*visual,'-t',scene['end']-scene['start'],'-vf',vf,'-an','-c:v','libx264','-preset','fast',
             '-crf','20','-threads','4','-pix_fmt','yuv420p','-r',FPS,output])
        print(f'Escena {i+1}/{len(scenes)} lista',flush=True)
    (BASE/'concat.txt').write_text('\n'.join(f"file 'clips/{i:02}.mp4'" for i in range(len(scenes))),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',BASE/'concat.txt','-c','copy',BASE/'video_sin_voz.mp4'])
    output=ROOT/'Entregables/Demostracion_Funcional_Walmart_Vision_20261021.mp4'
    run(['-i',BASE/'video_sin_voz.mp4','-i',BASE/'audio/AudioWalmart.mp3','-af',
         f'adelay={int(INTRO*1000)}:all=1,loudnorm=I=-16:TP=-1.5:LRA=11,apad',
         '-t',duration,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k',
         '-ar','48000','-movflags','+faststart',output])
    print(json.dumps(dict(output=str(output),bytes=output.stat().st_size,
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),duration=duration),indent=2),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    render(args.preview)
