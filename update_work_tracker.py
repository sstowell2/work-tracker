#!/usr/bin/env python3
"""Update an existing 'As Above, So Below' GitHub Pages index.html.

The original embedded photograph, existing localStorage key, all saved-workout
formats and the rest of the app are preserved. A backup is created first.

Usage (Windows): py update_work_tracker.py index.html
Usage (macOS/Linux): python3 update_work_tracker.py index.html
"""
from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
import sys


def modify(src: str) -> str:
    def once(old: str, new: str, label: str) -> None:
        nonlocal src
        count = src.count(old)
        if count != 1:
            raise ValueError(f"{label}: expected one exact match; found {count}. This updater expects the current GitHub version; no file was modified.")
        src = src.replace(old, new, 1)

    def fn(name: str, following: str, replacement: str) -> None:
        nonlocal src
        start = src.find('function '+name+'(')
        end = src.find('\n'+following, start)
        if start == -1 or end == -1:
            raise ValueError(f"Cannot locate {name}(). No file was modified.")
        src = src[:start]+replacement+src[end:]

    if "name:'Calisthenics'" in src and "data-day=\"3\"" in src:
        raise ValueError("This file already has the Day 4 update. No changes were needed.")
    if "data:image/jpeg;base64," not in src:
        raise ValueError("The original embedded photo was not found. No changes were made.")

    once('.day-tabs{display:grid;grid-template-columns:repeat(3,1fr);',
         '.day-tabs{display:grid;grid-template-columns:repeat(2,1fr);', 'four-day button layout')

    once('.app{position:relative;display:flex;',
         '''body:after{content:"";position:fixed;top:17%;right:12%;width:clamp(72px,18vw,116px);aspect-ratio:1;border-radius:50%;background:radial-gradient(circle at 33% 41%,rgba(80,98,118,.17) 0 6%,transparent 7%),radial-gradient(circle at 66% 66%,rgba(90,105,125,.18) 0 10%,transparent 11%),radial-gradient(circle at 62% 25%,rgba(118,128,140,.16) 0 7%,transparent 8%),radial-gradient(circle at 34% 28%,#fffef2,#e7e9e4 48%,#a4b2c0 80%,#7e91a6);box-shadow:0 0 23px 9px rgba(242,245,255,.34),0 0 90px 30px rgba(215,228,255,.22);pointer-events:none;z-index:0;opacity:.94}.app{z-index:1;position:relative;display:flex;''',
         'visible moon overlay')

    once('<button data-day="2">Day 3<br>Legs & Shoulders</button></div>',
         '<button data-day="2">Day 3<br>Legs & Shoulders</button><button data-day="3">Day 4<br>Calisthenics</button></div>', 'Day 4 tab')

    once('<strong id="volume">0</strong>Volume (lb)',
         '<strong id="volume">0</strong><span id="metricLabel">Volume (lb)</span>',
         'dynamic exercise metric label')

    once("notes:['Avoid locking knees','Slow, controlled repetitions','Avoid swinging','Use machine or dumbbells','Use light dumbbells']}\n];",
         """notes:['Avoid locking knees','Slow, controlled repetitions','Avoid swinging','Use machine or dumbbells','Use light dumbbells']},
 {name:'Calisthenics',items:['Plank','Mountain Climbers','Jumping Jacks','Push-ups','Bodyweight Squats'],notes:['Keep your body straight and brace your core','Alternate knees toward your chest with control','Land softly and keep a steady rhythm','Keep your body in one straight line; modify on knees if needed','Sit back and keep knees tracking over toes'],units:['seconds','seconds','reps','reps','reps'],goals:['30–60 seconds','30–45 seconds','30–50 reps','8–15 reps','15–20 reps']}
];""", 'new calisthenics exercise plan')

    once("state.days=DAYS.map((d,i)=>{const x=state.days[i]||emptyDay();x.sets=Array.from({length:20},(_,j)=>({...emptySet(),...(x.sets||[])[j],running:false}));return x});",
         "function normalizeDays(raw){return DAYS.map((d,i)=>{const x=(raw||[])[i]||emptyDay();x.sets=Array.from({length:20},(_,j)=>({...emptySet(),...(x.sets||[])[j],running:false}));return x})}\nstate.days=normalizeDays(state.days);",
         'compatibility with existing three-day storage')

    fn('updateStats', 'function syncTimer', '''function updateStats(){
const d=state.days[activeDay],count=d.sets.filter(x=>x.done).length;
$('progressNumber').textContent=count+'/20';$('progressBar').style.width=count*5+'%';
let total=0;
if(activeDay===3){d.sets.forEach((x,i)=>{if(x.done&&Math.floor(i/4)>=2&&x.reps!=='')total+=Number(x.reps)||0})}
else{d.sets.forEach((x,i)=>{if(x.done&&x.weight!==''&&x.reps!=='')total+=Number(x.weight)*Number(x.reps)*(activeDay===0&&Math.floor(i/4)>=2?2:1)})}
$('volume').textContent=total.toLocaleString();
}''')

    fn('render','function start', '''function render(){
const d=state.days[activeDay],plan=DAYS[activeDay],cali=activeDay===3;
document.querySelectorAll('[data-day]').forEach(b=>b.classList.toggle('selected',Number(b.dataset.day)===activeDay));
$('dayNote').textContent=cali?'Complete four sets of each movement. Enter seconds for timed exercises or reps for counted exercises, then check the set to start the 2-minute rest.':'Each exercise has four sets. Enter actual weight and reps after each set, then check it off.';
$('metricLabel').textContent=cali?'Reps completed':'Volume (lb)';
let html='';
plan.items.forEach((name,i)=>{
 const unit=cali?plan.units[i]:'reps';
 html+='<section class="exercise-block"><h3>'+(i+1)+'. '+escapeHtml(name)+'</h3><div class="muted">'+escapeHtml(plan.notes[i]+(cali?' · Goal: '+plan.goals[i]:' · Aim for 10–12 reps, adjust as needed'))+'</div>';
 for(let j=0;j<4;j++){
  const id=i*4+j,x=d.sets[id];clamp(x);
  const fields=cali?'<div><label>'+(unit==='seconds'?'Time (sec)':'Reps')+'</label><input type="number" min="0" step="1" inputmode="numeric" data-reps="'+id+'" value="'+escapeHtml(x.reps)+'" placeholder="'+(unit==='seconds'?'seconds':'reps')+'"></div>':'<div><label>Weight (lb)</label><input type="number" min="0" step="any" inputmode="decimal" data-weight="'+id+'" value="'+escapeHtml(x.weight)+'" placeholder="lbs"></div><div><label>Reps</label><input type="number" min="0" inputmode="numeric" data-reps="'+id+'" value="'+escapeHtml(x.reps)+'" placeholder="reps"></div>';
  html+='<div class="set-card'+(x.done?' done':'')+'" id="set-'+id+'"><div class="set-fields'+(cali?' cali-fields':'')+'"><input type="checkbox" aria-label="Complete '+escapeHtml(name)+' set '+(j+1)+'" data-check="'+id+'" '+(x.done?'checked':'')+'><div style="font-size:12px;font-weight:650;padding-bottom:12px">Set '+(j+1)+'</div>'+fields+'</div><div class="restline"><div><span class="muted" id="status-'+id+'">Rest timer</span><div class="clock" id="clock-'+id+'">'+format(x.remaining)+'</div></div><div><button id="toggle-'+id+'" data-toggle="'+id+'">'+(x.running?'Pause':'Start')+'</button> <button data-reset="'+id+'">Reset</button></div></div></div>';
 }
 html+='</section>';
});
$('exerciseList').innerHTML=html;
['cardioDone','speed','incline','minutes','walkingMiles','saunaDone','saunaMinutes'].forEach(k=>{$(k).type==='checkbox'?$(k).checked=!!d[k]:$(k).value=d[k]??''});
updateStats();
}''')

    once('.set-fields label{font-size:11px;',
         '.set-fields.cali-fields{grid-template-columns:26px 48px minmax(0,1fr)}.set-fields label{font-size:11px;',
         'calisthenics field layout')

    fn('logText', 'async function copy', '''function logText(d,day,finish=false){
const plan=DAYS[day];if(!plan)return 'Unknown workout day';
let lines=['Day '+(day+1)+' — '+plan.name+(finish?' (saved)':'')];
plan.items.forEach((name,i)=>{lines.push(name);for(let j=0;j<4;j++){
const x=d.sets[i*4+j]||emptySet(),value=x.reps===''?'—':x.reps;
const detail=day===3?value+' '+(plan.units[i]==='seconds'?'seconds':'reps'):(x.weight===''?'—':x.weight)+' lb × '+value+' reps';
lines.push((x.done?'✓':'☐')+' Set '+(j+1)+': '+detail+(x.restActual==null?'':' | rest '+x.restActual+' sec'));
}});
lines.push('Cardio: '+(d.cardioDone?'✓':'☐')+' '+(d.minutes||'—')+' min at '+(d.speed||'—')+' mph, '+(d.incline||'—')+'% incline; other walking '+(d.walkingMiles||'—')+' miles');
lines.push('Sauna: '+(d.saunaDone?'✓':'☐')+' '+(d.saunaMinutes||'—')+' min');
return lines.join('\\n');
}''')

    once('state=obj;state.days.forEach(d=>d.sets.forEach(s=>s.running=false));save();render();history();',
         'state=obj;state.days=normalizeDays(state.days);save();render();history();',
         'old backup import compatibility')

    assert 'data:image/jpeg;base64,' in src, 'Photo was accidentally lost'
    assert 'name:\'Calisthenics\'' in src and 'body:after{content:' in src
    return src


def main() -> int:
    p=argparse.ArgumentParser(description='Update your workout tracker without losing its original photo.')
    p.add_argument('index', nargs='?', default='index.html', help='Path to existing index.html')
    args=p.parse_args()
    target=Path(args.index).expanduser().resolve()
    if not target.is_file():
        print(f'ERROR: {target} does not exist. Place this script beside your downloaded index.html.')
        return 1
    original=target.read_text(encoding='utf-8')
    try:
        updated=modify(original)
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1
    backup=target.with_name(f'index-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}.html')
    backup.write_text(original,encoding='utf-8')
    target.write_text(updated,encoding='utf-8')
    print('SUCCESS: Updated index.html with Day 4 calisthenics and a moon!')
    print('Original backup:',backup)
    print('Updated file:',target)
    print('Upload only the updated index.html to your GitHub repository.')
    return 0

if __name__=='__main__':
    sys.exit(main())
