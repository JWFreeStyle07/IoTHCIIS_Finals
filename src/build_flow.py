"""
build_flow.py  –  generates nodered/flow.json cleanly
Run:  .\\venv\\Scripts\\python src\\build_flow.py
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "nodered" / "flow.json"

# ── HTML templates ────────────────────────────────────────────────────────────

STATS_HTML = """<div style='font-family:Inter,Arial,sans-serif;padding:6px 2px;'>
  <div style='margin-bottom:14px;'>
    <div style='font-size:22px;font-weight:700;color:#1A237E;'>Good Morning!</div>
    <div style='font-size:13px;color:#555;'>Here&rsquo;s today&rsquo;s patient follow-up overview &mdash; {{msg.payload.date}}</div>
  </div>
  <div style='display:flex;gap:10px;flex-wrap:wrap;'>
    <div style='flex:1;min-width:130px;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
        <div style='width:32px;height:32px;border-radius:8px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;font-size:17px;'>&#128197;</div>
        <div style='font-size:10px;color:#1D4ED8;font-weight:700;letter-spacing:.5px;'>CHECK-INS TODAY</div>
      </div>
      <div style='font-size:30px;font-weight:700;color:#1E3A8A;line-height:1.1;'>{{msg.payload.checkins}}</div>
      <div style='font-size:11px;color:#059669;margin-top:2px;'>&#8679; 12% vs. yesterday</div>
    </div>
    <div style='flex:1;min-width:130px;background:#F5F3FF;border:1px solid #DDD6FE;border-radius:10px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
        <div style='width:32px;height:32px;border-radius:8px;background:#EDE9FE;display:flex;align-items:center;justify-content:center;font-size:17px;'>&#128336;</div>
        <div style='font-size:10px;color:#7C3AED;font-weight:700;letter-spacing:.5px;'>UPCOMING</div>
      </div>
      <div style='font-size:30px;font-weight:700;color:#4C1D95;line-height:1.1;'>{{msg.payload.upcoming}}</div>
      <div style='font-size:11px;color:#059669;margin-top:2px;'>&#8679; 8% vs. yesterday</div>
    </div>
    <div style='flex:1;min-width:130px;background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
        <div style='width:32px;height:32px;border-radius:8px;background:#FEF3C7;display:flex;align-items:center;justify-content:center;font-size:17px;'>&#9888;</div>
        <div style='font-size:10px;color:#D97706;font-weight:700;letter-spacing:.5px;'>DUE</div>
      </div>
      <div style='font-size:30px;font-weight:700;color:#92400E;line-height:1.1;'>{{msg.payload.due}}</div>
      <div style='font-size:11px;color:#D97706;margin-top:2px;'>&#8679; 3% vs. yesterday</div>
    </div>
    <div style='flex:1;min-width:130px;background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
        <div style='width:32px;height:32px;border-radius:8px;background:#FEE2E2;display:flex;align-items:center;justify-content:center;font-size:17px;'>&#128683;</div>
        <div style='font-size:10px;color:#DC2626;font-weight:700;letter-spacing:.5px;'>OVERDUE</div>
      </div>
      <div style='font-size:30px;font-weight:700;color:#7F1D1D;line-height:1.1;'>{{msg.payload.overdue}}</div>
      <div style='font-size:11px;color:#DC2626;margin-top:2px;'>&#8679; 8% vs. yesterday</div>
    </div>
    <div style='flex:1;min-width:130px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
        <div style='width:32px;height:32px;border-radius:8px;background:#DCFCE7;display:flex;align-items:center;justify-content:center;font-size:17px;'>&#10003;</div>
        <div style='font-size:10px;color:#16A34A;font-weight:700;letter-spacing:.5px;'>VISITED</div>
      </div>
      <div style='font-size:30px;font-weight:700;color:#14532D;line-height:1.1;'>{{msg.payload.visited}}</div>
      <div style='font-size:11px;color:#059669;margin-top:2px;'>&#8679; 2% vs. yesterday</div>
    </div>
  </div>
</div>"""

PATIENT_TABLE_HTML = """<style>
.bbt{width:100%;border-collapse:collapse;font-family:Inter,Arial,sans-serif;font-size:12px;}
.bbt th{background:#F1F5F9;color:#475569;font-weight:600;padding:6px 8px;text-align:left;border-bottom:2px solid #E2E8F0;white-space:nowrap;}
.bbt td{padding:6px 8px;border-bottom:1px solid #F1F5F9;vertical-align:middle;white-space:nowrap;}
.bbt tr:hover td{background:#F8FAFC;}
.bdg{display:inline-block;padding:1px 9px;border-radius:20px;font-size:10.5px;font-weight:600;}
.up{background:#EEF2FF;color:#4F46E5;}
.du{background:#FFFBEB;color:#D97706;}
.ov{background:#FEF2F2;color:#DC2626;}
.vi{background:#F0FDF4;color:#16A34A;}
.av{width:26px;height:26px;border-radius:50%;background:#DBEAFE;display:inline-flex;align-items:center;justify-content:center;font-size:12px;margin-right:5px;vertical-align:middle;}
.ba{border:1px solid #CBD5E1;background:#fff;border-radius:5px;padding:2px 8px;font-size:10.5px;cursor:pointer;color:#1D4ED8;}
.sb{width:100%;padding:5px 10px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px;margin-bottom:7px;box-sizing:border-box;}
.fb{padding:3px 10px;border-radius:20px;border:1px solid #CBD5E1;background:#fff;font-size:11px;cursor:pointer;margin-right:3px;margin-bottom:4px;}
.fb.ac{background:#1E3A8A;color:#fff;border-color:#1E3A8A;}
</style>
<div style='font-family:Inter,Arial,sans-serif;padding:2px;'>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:7px;flex-wrap:wrap;'>
    <input class='sb' type='text' placeholder='&#128269; Search patient name or ID&hellip;' style='flex:1;min-width:200px;margin-bottom:0;'/>
    <div>
      <button class='fb ac'>All</button>
      <button class='fb'>Upcoming</button>
      <button class='fb'>Due</button>
      <button class='fb'>Overdue</button>
      <button class='fb'>Reminder Sent</button>
      <button class='fb'>Visited</button>
    </div>
  </div>
  <table class='bbt'>
    <thead><tr>
      <th>Patient</th><th>Patient ID</th><th>Condition</th>
      <th>Last Visit</th><th>Next Follow-up</th><th>Status</th><th>Action</th>
    </tr></thead>
    <tbody>
      <tr><td><span class='av'>&#128100;</span>Juan Dela Cruz</td><td style='color:#94A3B8;'>P-0016</td><td>Hypertension</td><td>Oct 15, 2025</td><td>Nov 20, 2026</td><td><span class='bdg up'>Upcoming</span></td><td><button class='ba'>&#128222; Contact</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Maria Santos</td><td style='color:#94A3B8;'>P-0034</td><td>Diabetes</td><td>Oct 10, 2025</td><td>Nov 18, 2025</td><td><span class='bdg du'>Due</span></td><td><button class='ba'>&#128222; Contact</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Pedro Reyes</td><td style='color:#94A3B8;'>P-0021</td><td>Tuberculosis</td><td>Oct 17, 2025</td><td>Nov 17, 2025</td><td><span class='bdg ov'>Overdue</span></td><td><button class='ba'>&#9993; Reminder</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Ana Garcia</td><td style='color:#94A3B8;'>P-0040</td><td>Hypertension</td><td>Oct 12, 2025</td><td>Oct 22, 2025</td><td><span class='bdg du'>Due</span></td><td><button class='ba'>&#128222; Contact</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Luis Navarro</td><td style='color:#94A3B8;'>P-0071</td><td>Diabetes</td><td>Oct 17, 2024</td><td>Nov 14, 2025</td><td><span class='bdg up'>Upcoming</span></td><td><button class='ba'>&#128065; View</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Carla Santos</td><td style='color:#94A3B8;'>P-0105</td><td>Hypertension</td><td>Nov 12, 2025</td><td>Dec 1, 2025</td><td><span class='bdg up'>Upcoming</span></td><td><button class='ba'>&#128065; View</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Ramon Cruz</td><td style='color:#94A3B8;'>P-0110</td><td>Tuberculosis</td><td>Nov 8, 2025</td><td>Nov 6, 2025</td><td><span class='bdg vi'>Visited</span></td><td><button class='ba'>&#128065; View</button></td></tr>
      <tr><td><span class='av'>&#128100;</span>Bea Lopez</td><td style='color:#94A3B8;'>P-0124</td><td>Diabetes</td><td>Nov 12, 2024</td><td>Nov 10, 2025</td><td><span class='bdg vi'>Visited</span></td><td><button class='ba'>&#128065; View</button></td></tr>
    </tbody>
  </table>
</div>"""

FORECAST_INFO_HTML = """<div style='font-family:Inter,Arial,sans-serif;padding:4px 6px;display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start;'>
  <!-- Peak hour -->
  <div style='flex:1;min-width:140px;background:#FFF3E0;border:1px solid #FFB300;border-radius:8px;padding:10px 12px;'>
    <div style='font-size:10px;color:#E65100;font-weight:700;letter-spacing:.5px;'>&#9650; PEAK HOUR</div>
    <div style='font-size:22px;font-weight:700;color:#BF360C;line-height:1.2;'>{{msg.payload.peakHour ? msg.payload.peakHour.hour : "--"}}:00</div>
    <div style='font-size:11px;color:#555;'>{{msg.payload.peakCount | number:1}} arrivals expected</div>
  </div>
  <!-- High-load alert -->
  <div ng-if='msg.payload.highWindows && msg.payload.highWindows.length > 0'
       style='flex:1;min-width:180px;background:#FFEBEE;border:1px solid #E53935;border-radius:8px;padding:10px 12px;'>
    <div style='font-size:10px;color:#B71C1C;font-weight:700;letter-spacing:.5px;'>&#9888; HIGH LOAD PREDICTED</div>
    <div style='font-size:12px;font-weight:600;color:#C62828;' ng-repeat='w in msg.payload.highWindows'>{{w}}</div>
  </div>
  <div ng-if='!msg.payload.highWindows || msg.payload.highWindows.length === 0'
       style='flex:1;min-width:180px;background:#E8F5E9;border:1px solid #A5D6A7;border-radius:8px;padding:10px 12px;'>
    <div style='font-size:10px;color:#1B5E20;font-weight:700;'>&#10003; ALL HOURS NORMAL</div>
    <div style='font-size:12px;color:#2E7D32;'>No high-load windows detected</div>
  </div>
  <!-- Forecast date -->
  <div style='flex:1;min-width:140px;background:#E3F2FD;border:1px solid #90CAF9;border-radius:8px;padding:10px 12px;'>
    <div style='font-size:10px;color:#0D47A1;font-weight:700;letter-spacing:.5px;'>&#128197; FORECAST DATE</div>
    <div style='font-size:14px;font-weight:700;color:#1565C0;'>{{msg.payload.date || "Waiting..."}}</div>
  </div>
  <!-- Quick actions -->
  <div style='flex:2;min-width:280px;'>
    <div style='font-size:11px;font-weight:700;color:#1A237E;margin-bottom:6px;'>Quick Actions</div>
    <div style='display:flex;gap:7px;flex-wrap:wrap;'>
      <div style='flex:1;min-width:120px;display:flex;align-items:center;justify-content:space-between;padding:7px 10px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;cursor:pointer;'>
        <div style='display:flex;align-items:center;gap:7px;'>
          <div style='width:26px;height:26px;border-radius:6px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;font-size:13px;'>&#128202;</div>
          <div><div style='font-size:11.5px;font-weight:600;color:#1E3A8A;'>Generate Forecast</div><div style='font-size:10px;color:#64748B;'>Update 24-hr prediction</div></div>
        </div><div style='color:#94A3B8;font-size:14px;'>&#8250;</div>
      </div>
      <div style='flex:1;min-width:120px;display:flex;align-items:center;justify-content:space-between;padding:7px 10px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;cursor:pointer;'>
        <div style='display:flex;align-items:center;gap:7px;'>
          <div style='width:26px;height:26px;border-radius:6px;background:#EDE9FE;display:flex;align-items:center;justify-content:center;font-size:13px;'>&#128196;</div>
          <div><div style='font-size:11.5px;font-weight:600;color:#4C1D95;'>View Reports</div><div style='font-size:10px;color:#64748B;'>Access detailed reports</div></div>
        </div><div style='color:#94A3B8;font-size:14px;'>&#8250;</div>
      </div>
      <div style='flex:1;min-width:120px;display:flex;align-items:center;justify-content:space-between;padding:7px 10px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;cursor:pointer;'>
        <div style='display:flex;align-items:center;gap:7px;'>
          <div style='width:26px;height:26px;border-radius:6px;background:#DCFCE7;display:flex;align-items:center;justify-content:center;font-size:13px;'>&#128101;</div>
          <div><div style='font-size:11.5px;font-weight:600;color:#14532D;'>Manage Patients</div><div style='font-size:10px;color:#64748B;'>Add or edit patients</div></div>
        </div><div style='color:#94A3B8;font-size:14px;'>&#8250;</div>
      </div>
    </div>
  </div>
</div>"""

FOOTER_HTML = """<div style='font-family:Inter,Arial,sans-serif;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:12px 18px;display:flex;align-items:center;gap:12px;'>
  <div style='font-size:20px;'>&#8505;</div>
  <div style='font-size:13px;color:#1E3A8A;'><b>BalikBisita</b> helps you stay on track with patient follow-ups and predicts patient volume for better preparation.</div>
</div>"""

# ── Function node JS ──────────────────────────────────────────────────────────

CHECKIN_JS = """
var now  = new Date();
var hour = now.getHours();
var base = (hour >= 8 && hour <= 17) ? 9 : 2;
var cnt  = Math.floor(Math.random() * base) + 1;

var history = flow.get('history') || [];
var entry   = {
    timestamp: new Date(now.getFullYear(), now.getMonth(),
                        now.getDate(), hour, 0, 0).toISOString().slice(0,19),
    count: cnt
};
history.push(entry);
if (history.length > 336) history = history.slice(history.length - 336);
flow.set('history', history);

var dayTotal = flow.get('dayTotal') || 0;
var lastHour = flow.get('lastHour');
if (lastHour !== hour) {
    if (hour === 0) { flow.set('dayTotal', 0); dayTotal = 0; }
    flow.set('lastHour', hour);
}
dayTotal += cnt;
flow.set('dayTotal', dayTotal);

var stats = { checkins: dayTotal, upcoming: 18, due: 7, overdue: 5, visited: 12 };
flow.set('stats', stats);

var days   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var dateStr = days[now.getDay()] + ', ' + months[now.getMonth()] + ' ' +
              now.getDate() + ', ' + now.getFullYear();

var statsMsg = { payload: {
    date: dateStr, checkins: stats.checkins,
    upcoming: stats.upcoming, due: stats.due,
    overdue: stats.overdue, visited: stats.visited
}};

var textMsg = { payload: entry.timestamp + '\u2002\u2002count: ' + cnt };

return [statsMsg, textMsg];
""".strip()

BUILD_REQ_JS = """
var history = flow.get('history') || [];
if (history.length < 24) {
    node.status({fill:'yellow',shape:'ring',text:'need '+history.length+'/24'});
    return null;
}
var now = new Date();
var tom = new Date(now); tom.setDate(tom.getDate()+1);
var yyyy = tom.getFullYear();
var mm   = String(tom.getMonth()+1).padStart(2,'0');
var dd   = String(tom.getDate()).padStart(2,'0');
node.status({fill:'blue',shape:'dot',text:'fetching '+yyyy+'-'+mm+'-'+dd});
msg.payload = { date: yyyy+'-'+mm+'-'+dd, history: history };
msg.headers = {'Content-Type':'application/json'};
return msg;
""".strip()

CHECK_RESP_JS = """
if (msg.statusCode !== 200 || !msg.payload || !msg.payload.forecasts) {
    node.status({fill:'red',shape:'dot',text:'unreachable'});
    return [null, {payload: '\u26a0\u2002Flask offline. Run: python src\\\\predict_service.py'}];
}
node.status({fill:'green',shape:'dot',text:'OK '+new Date().toLocaleTimeString()});
return [msg, null];
""".strip()

FORMAT_JS = """
var fc   = msg.payload.forecasts;
var date = msg.payload.date;
var HIGH = 5.0;

var labels = fc.map(function(f){ return f.hour+':00'; });
var values = fc.map(function(f){ return f.predicted_count; });

var highWindows = [];
var inW = false; var wS = null;
fc.forEach(function(f){
    if (f.predicted_count >= HIGH && !inW) { inW=true; wS=f.hour; }
    if (f.predicted_count <  HIGH &&  inW) { inW=false; highWindows.push(wS+':00\u2013'+f.hour+':00'); }
});
if (inW) highWindows.push(wS+':00\u201323:00');

var peak = fc.reduce(function(a,b){ return a.predicted_count>b.predicted_count?a:b; });

var chartMsg = {
    payload: [{ label: date, data: values }],
    labels : labels,
    topic  : date
};
var infoMsg = {
    payload: { date: date, peakHour: peak, peakCount: peak.predicted_count,
               highWindows: highWindows, forecasts: fc }
};
return [chartMsg, infoMsg];
""".strip()

# ── Assemble flow ─────────────────────────────────────────────────────────────

flow = [
  # tab
  {"id":"tab_bb","type":"tab","label":"BalikBisita Dashboard","disabled":False,"info":""},

  # ── Inject nodes ──────────────────────────────────────────────────────────
  {"id":"inj_tick","type":"inject","z":"tab_bb","name":"Tick every 10s",
   "props":[{"p":"payload"}],"repeat":"10","once":True,"onceDelay":1,
   "payload":"","payloadType":"date","x":130,"y":80,"wires":[["fn_checkin"]]},

  {"id":"inj_manual","type":"inject","z":"tab_bb","name":"Manual trigger",
   "props":[{"p":"payload"}],"repeat":"","once":False,
   "payload":"","payloadType":"date","x":130,"y":140,"wires":[["fn_build_req"]]},

  {"id":"inj_patients","type":"inject","z":"tab_bb","name":"Load patients once",
   "props":[{"p":"payload"}],"repeat":"","once":True,"onceDelay":0.5,
   "payload":"{}","payloadType":"json","x":130,"y":200,"wires":[["tpl_patients"]]},

  {"id":"inj_footer","type":"inject","z":"tab_bb","name":"Load footer once",
   "props":[{"p":"payload"}],"repeat":"","once":True,"onceDelay":0.5,
   "payload":"{}","payloadType":"json","x":130,"y":260,"wires":[["tpl_footer"]]},

  # ── Function nodes ────────────────────────────────────────────────────────
  {"id":"fn_checkin","type":"function","z":"tab_bb","name":"Simulate check-in",
   "func":CHECKIN_JS,"outputs":2,"x":360,"y":80,
   "wires":[["tpl_stats","fn_build_req"],["txt_checkin"]]},

  {"id":"fn_build_req","type":"function","z":"tab_bb","name":"Build forecast request",
   "func":BUILD_REQ_JS,"outputs":1,"x":590,"y":140,"wires":[["http_predict"]]},

  {"id":"fn_check_resp","type":"function","z":"tab_bb","name":"Check response",
   "func":CHECK_RESP_JS,"outputs":2,"x":850,"y":140,
   "wires":[["fn_format"],["txt_status"]]},

  {"id":"fn_format","type":"function","z":"tab_bb","name":"Format for dashboard",
   "func":FORMAT_JS,"outputs":2,"x":1060,"y":140,
   "wires":[["ui_chart"],["tpl_forecast_info"]]},

  # ── HTTP request ──────────────────────────────────────────────────────────
  {"id":"http_predict","type":"http request","z":"tab_bb","name":"POST /predict",
   "method":"POST","ret":"obj","paytoqs":"ignore",
   "url":"http://127.0.0.1:5000/predict","x":720,"y":140,"wires":[["fn_check_resp"]]},

  # ── Dashboard nodes ───────────────────────────────────────────────────────

  # Stats cards (ui_template – full width, no group header)
  {"id":"tpl_stats","type":"ui_template","z":"tab_bb","name":"Stats Cards",
   "group":"grp_stats","order":1,"width":0,"height":0,
   "format":STATS_HTML,
   "storeOutMessages":True,"fwdInMessages":True,"resendOnRefresh":True,
   "templateScope":"local","x":580,"y":80,"wires":[[]]},

  # Last check-in text (small, sits under stats)
  {"id":"txt_checkin","type":"ui_text","z":"tab_bb","group":"grp_stats",
   "order":2,"width":6,"height":1,"name":"Last check-in",
   "label":"Last simulated check-in","format":"{{msg.payload}}",
   "layout":"row-spread","x":580,"y":40,"wires":[]},

  # Service status text
  {"id":"txt_status","type":"ui_text","z":"tab_bb","group":"grp_stats",
   "order":3,"width":6,"height":1,"name":"Service status",   "label":"Forecast service","format":"{{msg.payload}}",
   "layout":"row-spread","x":1060,"y":220,"wires":[]},

  # Patient table (8/12 width)
  {"id":"tpl_patients","type":"ui_template","z":"tab_bb","name":"Patient Table",
   "group":"grp_patients","order":1,"width":0,"height":0,
   "format":PATIENT_TABLE_HTML,
   "storeOutMessages":False,"fwdInMessages":False,"resendOnRefresh":True,
   "templateScope":"local","x":360,"y":200,"wires":[[]]},

  # Forecast chart — full width, row 4
  {"id":"ui_chart","type":"ui_chart","z":"tab_bb","name":"Forecast Chart",
   "group":"grp_chart","order":1,"width":0,"height":7,
   "label":"","chartType":"line","legend":"false","xformat":"auto",
   "interpolate":"monotone","nodata":"Waiting for forecast data\u2026",
   "dot":True,"ymin":"0","ymax":"","removeOlder":1,"removeOlderPoints":"1",
   "removeOlderUnit":"604800","cutout":0,"useOneColor":True,
   "colors":["#1565C0","#E3F2FD","#90CAF9"],
   "outputs":0,"x":1280,"y":100,"wires":[]},

  # Forecast info panel + quick actions — full width, row 5
  {"id":"tpl_forecast_info","type":"ui_template","z":"tab_bb","name":"Forecast Info",
   "group":"grp_forecast","order":1,"width":0,"height":0,
   "format":FORECAST_INFO_HTML,
   "storeOutMessages":True,"fwdInMessages":True,"resendOnRefresh":True,
   "templateScope":"local","x":1280,"y":160,"wires":[[]]},

  # Footer banner (full width)
  {"id":"tpl_footer","type":"ui_template","z":"tab_bb","name":"Footer",
   "group":"grp_footer","order":1,"width":0,"height":0,
   "format":FOOTER_HTML,
   "storeOutMessages":False,"fwdInMessages":False,"resendOnRefresh":True,
   "templateScope":"local","x":360,"y":260,"wires":[[]]},

  # ── Groups ────────────────────────────────────────────────────────────────
  # Row 1: stat cards (full width, no header border)
  {"id":"grp_stats","type":"ui_group","name":"Overview",
   "tab":"ui_tab_main","order":1,"disp":False,"width":"12","collapse":False},

  # Row 2: patient table (full width)
  {"id":"grp_patients","type":"ui_group","name":"Patient Follow-up List",
   "tab":"ui_tab_main","order":2,"disp":True,"width":"12","collapse":False},

  # Row 3: footer banner (full width, no header)
  {"id":"grp_footer","type":"ui_group","name":"",
   "tab":"ui_tab_main","order":3,"disp":False,"width":"12","collapse":False},

  # Row 4: forecast chart (full width)
  {"id":"grp_chart","type":"ui_group","name":"24-Hour Patient Forecast",
   "tab":"ui_tab_main","order":4,"disp":True,"width":"12","collapse":False},

  # Row 5: forecast info + quick actions (full width, no header)
  {"id":"grp_forecast","type":"ui_group","name":"",
   "tab":"ui_tab_main","order":5,"disp":False,"width":"12","collapse":False},

  # ── Tab ───────────────────────────────────────────────────────────────────
  {"id":"ui_tab_main","type":"ui_tab","name":"BalikBisita Dashboard",
   "icon":"dashboard","order":1,"disabled":False,"hidden":False},
]

OUT.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Flow written to {OUT}")
