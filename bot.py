from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    PollAnswerHandler,
)
import time

# ================= TOKEN =================
TOKEN = "8201199125:AAH4Z9gAeLW3J09-G57gEkb39gu54KGizOI"

# ================= SETTINGS =================
QUIZ_INTERVAL = 7200          # 2 hours
NIGHT_START = 0               # 12 AM
NIGHT_END = 6                 # 6 AM

# ================= STORAGE =================
GROUPS = set()
WORLD_SCORES = {}             # user_id -> points
GROUP_SCORES = {}             # chat_id -> {user_id -> points}
POLL_DATA = {}                # poll_id -> {correct, chat_id}
CURRENT_Q_INDEX = 0

# ================= HELPERS =================
def display_name(user):
    if user.username:
        return f"@{user.username}"
    return f"[{user.first_name}](tg://user?id={user.id})"

def is_night():
    h = time.localtime().tm_hour
    return NIGHT_START <= h < NIGHT_END

# ================= QUESTIONS (120 UNIQUE) =================
QUESTIONS = [
    # -------- Batch 1: Q1–Q60 --------
    {"q":"SI unit of work is","o":["Watt","Joule","Newton","Pascal"],"c":1},
    {"q":"Which quantity is scalar?","o":["Velocity","Acceleration","Momentum","Speed"],"c":3},
    {"q":"Dimensional formula of acceleration is","o":["LT⁻¹","LT⁻²","L²T⁻¹","MLT⁻²"],"c":1},
    {"q":"Newton’s first law is law of","o":["Force","Gravitation","Inertia","Momentum"],"c":2},
    {"q":"Area under velocity–time graph represents","o":["Acceleration","Speed","Displacement","Momentum"],"c":2},
    {"q":"A body at rest can have","o":["Zero v & zero a","Zero v & non-zero a","Non-zero v & zero a","Both non-zero"],"c":1},
    {"q":"Which is a vector quantity?","o":["Mass","Time","Force","Energy"],"c":2},
    {"q":"Unit of momentum is","o":["kg m s⁻¹","N s⁻¹","J s","kg m² s⁻²"],"c":0},
    {"q":"A freely falling body moves with","o":["Constant speed","Constant velocity","Uniform acceleration","Variable acceleration"],"c":2},
    {"q":"Slope of velocity–time graph gives","o":["Velocity","Displacement","Acceleration","Force"],"c":2},

    {"q":"Work done by centripetal force is","o":["Maximum","Minimum","Zero","Infinite"],"c":2},
    {"q":"A particle in circular motion has","o":["Constant velocity","Zero acceleration","Changing velocity","Zero force"],"c":2},
    {"q":"Momentum is conserved when","o":["External force constant","External force zero","Internal forces act","Acceleration zero"],"c":1},
    {"q":"If velocity is doubled, kinetic energy becomes","o":["2×","3×","4×","8×"],"c":2},
    {"q":"Dimension of force is","o":["MLT⁻¹","ML²T⁻²","MLT⁻²","M²LT⁻²"],"c":2},
    {"q":"For uniform circular motion, acceleration is","o":["Tangential","Radial inward","Radial outward","Zero"],"c":1},
    {"q":"Uniform motion shows which graph?","o":["Curved x–t","Straight x–t","Curved v–t","Horizontal a–t"],"c":1},
    {"q":"Impulse equals change in","o":["Energy","Velocity","Momentum","Power"],"c":2},
    {"q":"At highest point of vertical throw, acceleration is","o":["Zero","g upward","g downward","Variable"],"c":2},
    {"q":"Friction acts","o":["Along motion","Opposite to relative motion","Downward","Upward"],"c":1},

    {"q":"Constant speed but variable velocity occurs in","o":["Straight line","Constant a","Circular path","Zero a"],"c":2},
    {"q":"If net external force is zero, conserved is","o":["Kinetic energy","Velocity","Momentum","Acceleration"],"c":2},
    {"q":"Maximum range of projectile at angle","o":["30°","45°","60°","90°"],"c":1},
    {"q":"Unit of angular momentum is","o":["kg m s⁻¹","kg m² s⁻¹","N m","J s⁻¹"],"c":1},

    {"q":"SI unit of electric charge","o":["Ampere","Volt","Coulomb","Farad"],"c":2},
    {"q":"Ohm’s law valid when","o":["Temp varies","Physical conditions constant","Current large","Voltage zero"],"c":1},
    {"q":"Unit of electric field","o":["J/C","V s","N/C","C/N"],"c":2},
    {"q":"Electric field inside conductor is","o":["Infinite","Zero","Maximum","Variable"],"c":1},
    {"q":"SI unit of resistance","o":["Volt","Ohm","Ampere","Farad"],"c":1},

    {"q":"Drift velocity order","o":["10⁶","10⁻³","10²","10⁴"],"c":1},
    {"q":"Kirchhoff loop law based on","o":["Charge","Energy","Momentum","Mass"],"c":1},
    {"q":"Resistance depends on","o":["Length","Area","Material","All"],"c":3},
    {"q":"PE of like charges is","o":["Negative","Zero","Positive","Infinite"],"c":2},
    {"q":"With dielectric & battery connected, constant is","o":["Charge","Capacitance","Energy","Voltage"],"c":3},

    {"q":"Magnetic force zero when velocity is","o":["Parallel to field","Perpendicular","Opposite","Any"],"c":0},
    {"q":"Lenz law follows conservation of","o":["Charge","Energy","Momentum","Mass"],"c":1},
    {"q":"Transformer principle","o":["Self induction","Mutual induction","Electrostatics","Ohm law"],"c":1},
    {"q":"AC frequency in India","o":["25 Hz","50 Hz","60 Hz","100 Hz"],"c":1},

    {"q":"Power is rate of change of","o":["Force","Energy","Velocity","Momentum"],"c":1},
    {"q":"Unit of power","o":["Joule","Newton","Watt","Pascal"],"c":2},
    {"q":"Elastic collision conserves","o":["Momentum only","Energy only","Both KE & momentum","Neither"],"c":2},
    {"q":"Zero velocity but non-zero acceleration at","o":["Uniform motion","Top of vertical motion","Rough surface","Circular motion"],"c":1},
    {"q":"Dimension of Planck constant","o":["ML²T⁻¹","ML²T⁻²","MLT⁻¹","MLT⁻²"],"c":0},
    {"q":"Electric current is rate of flow of","o":["Energy","Charge","Voltage","Power"],"c":1},

    {"q":"Same range for angles θ and","o":["30°−θ","90°−θ","180°−θ","2θ"],"c":1},
    {"q":"Torque zero when force is","o":["Parallel to lever arm","Perpendicular","At centre","Anywhere"],"c":0},
    {"q":"Moment of inertia depends on","o":["Mass","Axis","Distribution","All"],"c":3},
    {"q":"Charged particle ⟂ B-field path","o":["Straight","Parabolic","Circular","Helical"],"c":2},

    {"q":"Unit of capacitance","o":["Ohm","Volt","Farad","Coulomb"],"c":2},
    {"q":"Unit of magnetic flux","o":["Tesla","Weber","Henry","Ampere"],"c":1},
    {"q":"EMF is work per unit","o":["Charge","Current","Resistance","Power"],"c":0},
    {"q":"Fuse wire has","o":["High R & low mp","Low R & high mp","Zero R","High mp"],"c":0},
    {"q":"Electric power equals","o":["VI","V/I","I/V","IR"],"c":0},
    {"q":"Frame-independent quantity","o":["Velocity","Acceleration","Distance","Displacement"],"c":2},
    {"q":"Maximum inertia","o":["Bicycle","Car","Truck","Scooter"],"c":2},
    {"q":"Gravitational force is","o":["Repulsive","Attractive","Zero","Variable"],"c":1},
    {"q":"Unit of pressure","o":["N m","N/m","N/m²","kg m s⁻¹"],"c":2},
    {"q":"Law giving F=ma","o":["First","Second","Third","Gravitation"],"c":1},
    {"q":"Momentum of body at rest","o":["Maximum","Minimum","Zero","Infinite"],"c":2},
    {"q":"Work zero when force is","o":["Perpendicular to displacement","Parallel","Opposite","At angle"],"c":0},

    # -------- Batch 2: Q61–Q120 --------
    {"q":"Quantity with magnitude & direction","o":["Speed","Distance","Velocity","Time"],"c":2},
    {"q":"SI unit of power","o":["Joule","Watt","Newton","Pascal"],"c":1},
    {"q":"Slope of a–t graph gives","o":["Velocity","Displacement","Jerk","Force"],"c":2},
    {"q":"Uniform straight motion has","o":["Variable speed","Constant a","Zero a","Variable v"],"c":2},
    {"q":"Conserved in all collisions","o":["KE","PE","Momentum","Speed"],"c":2},
    {"q":"Unit of angular velocity","o":["rad s⁻¹","m s⁻¹","N m","J s"],"c":0},
    {"q":"Constant acceleration graph","o":["Straight x–t","Straight v–t","Curved v–t","Curved a–t"],"c":1},
    {"q":"Value of g on Earth","o":["9.8","8.9","10.8","9.0"],"c":0},
    {"q":"Negative work when force is","o":["Parallel","Perpendicular","Opposite","Zero"],"c":2},
    {"q":"Contact force","o":["Gravitational","Magnetic","Electrostatic","Friction"],"c":3},

    {"q":"Centripetal acceleration direction","o":["Along v","Away","Towards centre","Tangential"],"c":2},
    {"q":"Projectile horizontal acceleration","o":["g","Zero","Constant","Variable"],"c":1},
    {"q":"Torque dimension equals","o":["Force","Energy","Power","Momentum"],"c":1},
    {"q":"Kinetic energy formula","o":["mv²","½mv²","2mv²","v²/m"],"c":1},
    {"q":"Uniform circular motion constant","o":["Velocity","Acceleration","Speed","Force"],"c":2},
    {"q":"Impulse–momentum relates to","o":["Velocity","Force","Momentum","Energy"],"c":2},
    {"q":"At highest point (throw)","o":["v=0,a=0","v=0,a=g↓","v=g↑","Both non-zero"],"c":1},
    {"q":"Work area graph","o":["v–t","x–t","F–x","a–t"],"c":2},
    {"q":"Displacement can be zero when distance is","o":["Always","Never","Non-zero","Equal"],"c":2},
    {"q":"SI unit of pressure","o":["N","N/m","N/m²","kg m s⁻¹"],"c":2},

    {"q":"Same KE, momenta ratio (m & 2m)","o":["1:2","√2:1","1:√2","2:1"],"c":1},
    {"q":"v ∝ t implies acceleration","o":["Zero","Constant","Increasing","Decreasing"],"c":1},
    {"q":"Max range angle","o":["30°","45°","60°","90°"],"c":1},
    {"q":"Zero work implies force","o":["Zero","Perpendicular","Parallel","Opposite"],"c":1},
    {"q":"Elastic collision conserves","o":["p only","KE only","Both","Neither"],"c":2},

    {"q":"SI unit of electric potential","o":["Joule","Volt","Coulomb","Ampere"],"c":1},
    {"q":"Current measured by","o":["Voltmeter","Galvanometer","Ammeter","Ohmmeter"],"c":2},
    {"q":"Free electrons due to","o":["Temp","Low R","Weak binding","High V"],"c":2},
    {"q":"Unit of capacitance","o":["Ohm","Farad","Weber","Henry"],"c":1},
    {"q":"Field lines originate from","o":["Negative","Positive","Both","Neutral"],"c":1},

    {"q":"Doubling length doubles resistance","o":["True","False","Depends","NA"],"c":0},
    {"q":"Metal resistance with temperature","o":["Decreases","Same","Increases","Zero"],"c":2},
    {"q":"Junction law based on","o":["Energy","Momentum","Charge","Mass"],"c":2},
    {"q":"Electric power formula","o":["V/I","I²R","R/I²","V²/I"],"c":1},
    {"q":"Potential difference is work per unit","o":["Charge","Current","Energy","Power"],"c":0},

    {"q":"Charged particle ⟂ B-field path","o":["Straight","Parabolic","Circular","Helical"],"c":2},
    {"q":"Induced current direction by","o":["LHR","RHR","Lenz","Ampere"],"c":2},
    {"q":"Transformer works with","o":["DC","AC","Both","High V"],"c":1},
    {"q":"Self inductance depends on","o":["Current","Rate","Geometry","EMF"],"c":2},
    {"q":"Magnetic flux unit","o":["Tesla","Weber","Henry","Ampere"],"c":1},

    {"q":"Frame-independent quantity","o":["Velocity","Acceleration","Distance","Displacement"],"c":2},
    {"q":"Fuse wire property","o":["High R & low mp","Low R & high mp","Zero R","High mp"],"c":0},
    {"q":"Unit of magnetic field","o":["Weber","Tesla","Henry","Gauss"],"c":1},
    {"q":"EMF meaning","o":["Terminal V","Work/charge","Power","Resistance"],"c":1},
    {"q":"Unchanged on reversing current","o":["B-field dir","Heating effect","Force dir","EMF"],"c":1},

    {"q":"Satellite revolves because","o":["No force","Gravity provides centripetal","Magnetic","Inertia"],"c":1},
    {"q":"Torque depends on","o":["Force","Distance","Force & perp dist","Mass"],"c":2},
    {"q":"Circular motion constant","o":["Net force zero","Velocity","a magnitude","Zero a"],"c":2},
    {"q":"Pendulum period depends on","o":["Mass","Length","Amplitude","Shape"],"c":1},
    {"q":"Energy dimension","o":["MLT⁻²","ML²T⁻²","ML²T⁻¹","M²LT⁻²"],"c":1},

    {"q":"Recoil explained by","o":["First","Second","Third","Gravitation"],"c":2},
    {"q":"Always positive","o":["Velocity","Displacement","Distance","Acceleration"],"c":2},
    {"q":"Angular momentum unit","o":["kg m s⁻¹","kg m² s⁻¹","N m","J s"],"c":1},
    {"q":"Electrical to mechanical","o":["Generator","Transformer","Motor","Rectifier"],"c":2},
    {"q":"Gravitational force","o":["Repulsive","Attractive","Zero","Variable"],"c":1},
    {"q":"ML²T⁻³ quantity","o":["Energy","Power","Momentum","Force"],"c":1},
    {"q":"Heat ∝ I²Rt: doubling I gives","o":["2×","3×","4×","½"],"c":2},
    {"q":"Voltmeter connected in","o":["Series","Parallel","Both","Any"],"c":1},
    {"q":"Electromagnetic wave","o":["Sound","Water","Light","Seismic"],"c":2},
    {"q":"Henry measures","o":["Resistance","Capacitance","Inductance","Flux"],"c":2},
]

# ×2 for ~20 days
QUESTIONS = QUESTIONS * 2

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group","supergroup"]:
        GROUPS.add(chat.id)
        GROUP_SCORES.setdefault(chat.id, {})
    await update.message.reply_text("🍎 Newton Quiz is live!")

# ================= AUTO QUIZ =================
async def auto_quiz(context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_Q_INDEX
    if is_night() or not GROUPS:
        return
    q = QUESTIONS[CURRENT_Q_INDEX]
    CURRENT_Q_INDEX = (CURRENT_Q_INDEX + 1) % len(QUESTIONS)
    for chat_id in GROUPS:
        poll = await context.bot.send_poll(
            chat_id=chat_id,
            question=q["q"],
            options=q["o"],
            type="quiz",
            correct_option_id=q["c"],
            is_anonymous=False
        )
        POLL_DATA[poll.poll.id] = {"correct": q["c"], "chat_id": chat_id}

# ================= ANSWERS =================
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.poll_answer
    if ans.poll_id not in POLL_DATA:
        return
    chat_id = POLL_DATA[ans.poll_id]["chat_id"]
    correct = POLL_DATA[ans.poll_id]["correct"]
    user = ans.user

    WORLD_SCORES.setdefault(user.id, 0)
    GROUP_SCORES.setdefault(chat_id, {}).setdefault(user.id, 0)

    if ans.option_ids[0] == correct:
        WORLD_SCORES[user.id] += 4
        GROUP_SCORES[chat_id][user.id] += 4
        msg = f"{display_name(user)} 🔥 (+4)"
    else:
        WORLD_SCORES[user.id] -= 1
        GROUP_SCORES[chat_id][user.id] -= 1
        msg = f"{display_name(user)} 😅 (−1)"

    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

# ================= LEADERBOARDS =================
async def toppers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = sorted(WORLD_SCORES.items(), key=lambda x:x[1], reverse=True)[:10]
    text = "🏆 Top 10 Toppers (World)\n\n"
    for i,(uid,pts) in enumerate(top,1):
        text += f"{i}. [User](tg://user?id={uid}) — {pts}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def group_toppers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in GROUP_SCORES:
        await update.message.reply_text("No data yet.")
        return
    top = sorted(GROUP_SCORES[chat_id].items(), key=lambda x:x[1], reverse=True)[:10]
    text = "🏆 Top 10 Toppers (This Group)\n\n"
    for i,(uid,pts) in enumerate(top,1):
        text += f"{i}. [User](tg://user?id={uid}) — {pts}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("toppers", toppers))
app.add_handler(CommandHandler("group_toppers", group_toppers))
app.add_handler(PollAnswerHandler(handle_poll_answer))
app.job_queue.run_repeating(auto_quiz, interval=QUIZ_INTERVAL, first=10)

print("Newton Quiz running...")
app.run_polling()
