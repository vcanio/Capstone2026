"""Genera la Gantt histórica y de cierre por semanas de referencia del equipo.

Usa matplotlib. La escala académica no inventa fechas diarias de agosto.
Los datos y su procedencia están versionados junto al gráfico.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Documentacion/Evidencias/planificacion_20261020.json'
TARGET = SOURCE.with_name('gantt_20261020.png')


def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':16})
    fig, ax = plt.subplots(figsize=(14, 8.0), dpi=160)
    fig.subplots_adjust(left=.40, right=.985, top=.80, bottom=.19)
    rows = data['hitos']
    for index, row in enumerate(rows):
        proposed = row['desde'] >= 12
        ax.barh(index, row['hasta']-row['desde']+.78, left=row['desde']-.39,
                height=.56, color='#E2E8EF' if proposed else '#355E7D',
                edgecolor='#657787' if proposed else '#355E7D', hatch='///' if proposed else None,
                linewidth=.8, zorder=3)
    ax.set_yticks(range(len(rows)), [f"{r['id']}  {r['actividad']}" for r in rows], fontsize=16)
    ax.tick_params(axis='y', length=0, pad=13)
    ax.set_xticks(range(1,18))
    ax.tick_params(axis='x', length=0, labelsize=16, pad=12)
    ax.xaxis.tick_top()
    ax.set_xlim(.5,17.5)
    ax.set_ylim(len(rows)-.4,-.7)
    ax.set_axisbelow(True)
    ax.grid(axis='x',color='#D4DCE4', linewidth=.8)
    for index in range(len(rows)+1):ax.axhline(index-.5, color='#EEF1F5',linewidth=.6,zorder=0)
    ax.axvline(11.5,color='#101B27',linewidth=1.3,linestyle=(0,(4,3)),zorder=4)
    for spine in ax.spines.values():spine.set_visible(False)
    fig.text(.035,.952,'Carta Gantt histórica y propuesta de cierre',fontsize=25,weight='bold',color='black')
    fig.text(.035,.906,'Inicio aproximado en agosto de 2026 · Corte al 20 de octubre · Semanas de referencia del equipo',fontsize=15,color='#364756')
    fig.text(.40,.852,'Semana',fontsize=14,color='#364756')
    fig.legend(handles=[Patch(facecolor='#355E7D',label='Trabajo realizado / prototipo operativo'),
                        Patch(facecolor='#E2E8EF',edgecolor='#657787',hatch='///',label='Trabajo futuro propuesto')],
               loc='lower left',bbox_to_anchor=(.03,.075),frameon=False,ncol=2,fontsize=14)
    fig.text(.035,.057,'Detección de bordes: inicio S9 e integración con YOLO en S11. Línea discontinua: corte de planificación.',fontsize=12.5,color='#364756')
    fig.text(.035,.022,'Inicio exacto por confirmar. Cierre sujeto a acuerdo. Defensa propuesta: 3–4 de diciembre.',fontsize=12.5,color='#364756')
    fig.savefig(TARGET,facecolor='white')
    plt.close(fig)
    print(TARGET)


if __name__ == '__main__':
    main()
