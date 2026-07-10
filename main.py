"""
main.py — FitAI Mobile App
6 screens: Setup, Dashboard, Plan, Active Workout, Stats, AI Insights
Light/Dark mode · Rest days · Start Workout flow · Plan persistence
"""

import os, sys, json
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'  # Fix Windows graphics driver issue
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.clock import Clock

import database as db
import theme as th
from recommender import HybridRecommender

Window.size = (400, 780)

rec = HybridRecommender()

# ─────────────────────────────────────────────────────────────────────────────
#  UI PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────

CLEAR = [0, 0, 0, 0]
PAD   = dp(16)
RAD   = dp(12)
NAV_H = dp(60)


def bg(widget, color, radius=RAD):
    with widget.canvas.before:
        Color(rgba=color)
        widget._bg = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
                size=lambda w, v: setattr(w._bg, 'size', v))
    return widget


def border(widget, color=None, radius=RAD, width=1):
    color = color or th.get('border')
    with widget.canvas.after:
        Color(rgba=color)
        widget._bdr = Line(
            rounded_rectangle=(widget.x, widget.y, widget.width, widget.height, radius),
            width=width
        )
    widget.bind(
        pos=lambda w, v: setattr(w._bdr, 'rounded_rectangle',
                                 (v[0], v[1], w.width, w.height, radius)),
        size=lambda w, v: setattr(w._bdr, 'rounded_rectangle',
                                  (w.x, w.y, v[0], v[1], radius)),
    )
    return widget


def lbl(text, size=14, color=None, bold=False, halign='left', height=None):
    color = color or th.get('text')
    l = Label(text=text, font_size=sp(size), color=color, bold=bold,
              halign=halign, size_hint_y=None,
              height=height or dp(max(size * 1.9, 24)))
    l.bind(width=lambda w, v: setattr(w, 'text_size', (v, None)))
    return l


def primary_btn(text, on_press=None, height=dp(48)):
    btn = Button(
        text=text, font_size=sp(14), bold=True,
        size_hint=(1, None), height=height,
        background_color=CLEAR, background_normal='',
        color=(1, 1, 1, 1),
    )
    bg(btn, th.get('blue'), radius=RAD)
    if on_press:
        btn.bind(on_press=on_press)
    return btn


def secondary_btn(text, on_press=None, height=dp(42)):
    btn = Button(
        text=text, font_size=sp(13),
        size_hint=(1, None), height=height,
        background_color=CLEAR, background_normal='',
        color=th.get('text2'),
    )
    bg(btn, th.get('card'), radius=RAD)
    border(btn, th.get('border'), radius=RAD)
    if on_press:
        btn.bind(on_press=on_press)
    return btn


def card(height=None, padding=PAD):
    c = BoxLayout(orientation='vertical', padding=padding,
                  size_hint_y=None, spacing=dp(8))
    bg(c, th.get('card'), radius=RAD)
    border(c, th.get('border'), radius=RAD)
    if height:
        c.height = height
    else:
        c.bind(minimum_height=c.setter('height'))
    return c


def divider():
    d = BoxLayout(size_hint=(1, None), height=dp(1))
    with d.canvas:
        Color(rgba=th.get('divider'))
        r = Rectangle(pos=d.pos, size=d.size)
    d.bind(pos=lambda w, v: setattr(r, 'pos', v),
           size=lambda w, v: setattr(r, 'size', v))
    return d


def inp(hint='', input_type='text', height=dp(44)):
    i = TextInput(
        hint_text=hint, multiline=False, input_type=input_type,
        font_size=sp(14), size_hint_y=None, height=height,
        background_color=th.get('surface'),
        foreground_color=th.get('text'),
        hint_text_color=th.get('text3'),
        cursor_color=th.get('blue'),
        padding=[dp(12), dp(10)],
    )
    border(i, th.get('border'), radius=dp(8))
    return i


def tag_lbl(text, color=None):
    color = color or th.get('blue')
    l = lbl(text, size=11, color=color, halign='center', height=dp(22))
    return l


def section_hdr(text):
    return lbl(text.upper(), size=10, color=th.get('text3'), bold=True, height=dp(20))


# ─────────────────────────────────────────────────────────────────────────────
#  BOTTOM NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

TABS = [
    ('dashboard', 'Dashboard'),
    ('plan',      'Plan'),
    ('workout',   'Workout'),
    ('stats',     'Stats'),
    ('insights',  'AI'),
]


class BottomNav(BoxLayout):
    def __init__(self, active, sm, **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None),
                         height=NAV_H, **kwargs)
        bg(self, th.get('nav_bg'), radius=0)

        # Top border
        with self.canvas.after:
            Color(rgba=th.get('border'))
            self._top = Line(points=[0, self.top, self.width, self.top], width=1)
        self.bind(pos=self._update_line, size=self._update_line)

        for name, label in TABS:
            is_active = name == active
            col = th.get('nav_active') if is_active else th.get('nav_inactive')
            btn = Button(
                text=label, font_size=sp(11), bold=is_active,
                color=col,
                background_color=CLEAR, background_normal='',
            )
            btn.bind(on_press=lambda b, s=name: setattr(sm, 'current', s))
            self.add_widget(btn)

    def _update_line(self, *_):
        self._top.points = [self.x, self.top, self.right, self.top]


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER BAR
# ─────────────────────────────────────────────────────────────────────────────

def make_header(title, subtitle='', right_widget=None):
    h = BoxLayout(orientation='vertical', size_hint=(1, None),
                  height=dp(72), padding=[PAD, dp(10), PAD, dp(8)])
    bg(h, th.get('header'), radius=0)

    row = BoxLayout(orientation='horizontal')
    t = lbl(title, size=20, color=(1, 1, 1, 1), bold=True, height=dp(30))
    row.add_widget(t)
    if right_widget:
        row.add_widget(right_widget)
    h.add_widget(row)

    if subtitle:
        s = lbl(subtitle, size=11, color=(0.7, 0.75, 0.85, 1), height=dp(18))
        h.add_widget(s)

    return h


# ─────────────────────────────────────────────────────────────────────────────
#  SETUP SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class SetupScreen(Screen):
    def __init__(self, sm, **kwargs):
        super().__init__(name='setup', **kwargs)
        self.sm = sm
        self._level = 'beginner'
        self._goal  = 'general_fitness'
        self._lbtns = {}
        self._gbtns = {}
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        bg(root, th.get('bg'), radius=0)

        # Header
        root.add_widget(make_header('FitAI', 'Personalized AI Workout Coach'))

        scroll = ScrollView()
        inner  = BoxLayout(orientation='vertical', padding=[PAD, dp(20), PAD, dp(20)],
                           spacing=dp(14), size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(lbl('Create your profile', size=18, bold=True, height=dp(28)))
        inner.add_widget(lbl('Enter your details to receive a personalized AI plan.',
                             size=13, color=th.get('text2'), height=dp(20)))
        inner.add_widget(divider())

        # Name
        inner.add_widget(section_hdr('Full Name'))
        self.i_name = inp('e.g. Haruna Josiah')
        inner.add_widget(self.i_name)

        # Age / Weight / Height
        row = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(80))
        for attr, label, hint in [('i_age','Age','25'),('i_wt','Weight kg','70'),('i_ht','Height cm','175')]:
            col = BoxLayout(orientation='vertical', spacing=dp(4))
            col.add_widget(section_hdr(label))
            i = inp(hint, input_type='number')
            setattr(self, attr, i)
            col.add_widget(i)
            row.add_widget(col)
        inner.add_widget(row)

        # Fitness level
        inner.add_widget(section_hdr('Fitness Level'))
        lrow = BoxLayout(orientation='horizontal', spacing=dp(8),
                         size_hint_y=None, height=dp(40))
        for lvl in ['beginner', 'intermediate', 'advanced']:
            b = self._toggle(lvl.capitalize(), lvl == self._level,
                             lambda bt, l=lvl: self._set_level(l))
            self._lbtns[lvl] = b
            lrow.add_widget(b)
        inner.add_widget(lrow)

        # Goal
        inner.add_widget(section_hdr('Training Goal'))
        grow = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(90))
        for key, label in [('muscle_gain','Muscle Gain'),('fat_loss','Fat Loss'),
                            ('endurance','Endurance'),('general_fitness','General Fitness')]:
            b = self._toggle(label, key == self._goal,
                             lambda bt, g=key: self._set_goal(g))
            self._gbtns[key] = b
            grow.add_widget(b)
        inner.add_widget(grow)

        self.err = lbl('', size=12, color=th.get('red'), halign='center', height=dp(20))
        inner.add_widget(self.err)

        self.submit = primary_btn('Create Profile', on_press=self._submit)
        inner.add_widget(self.submit)

        scroll.add_widget(inner)
        root.add_widget(scroll)
        self.add_widget(root)

    def _toggle(self, label, active, cb):
        col = th.get('blue') if active else th.get('text2')
        b   = Button(text=label, font_size=sp(12), bold=active,
                     size_hint=(1, 1),
                     background_color=CLEAR, background_normal='', color=col)
        bg(b, th.get('blue_dim') if active else th.get('surface'), radius=dp(8))
        border(b, th.get('blue') if active else th.get('border'), radius=dp(8))
        b.bind(on_press=cb)
        return b

    def _refresh_toggle(self, btn_dict, selected):
        for key, b in btn_dict.items():
            active = key == selected
            b.color = th.get('blue') if active else th.get('text2')
            b.bold  = active
            b.canvas.before.clear()
            bg(b, th.get('blue_dim') if active else th.get('surface'), radius=dp(8))
            b.canvas.after.clear()
            border(b, th.get('blue') if active else th.get('border'), radius=dp(8))

    def _set_level(self, l): self._level = l; self._refresh_toggle(self._lbtns, l)
    def _set_goal(self, g):  self._goal  = g; self._refresh_toggle(self._gbtns, g)

    def _submit(self, *_):
        name = self.i_name.text.strip()
        age  = self.i_age.text.strip()
        wt   = self.i_wt.text.strip()
        ht   = self.i_ht.text.strip()

        if not all([name, age, wt, ht]):
            self.err.text = 'Please fill in all fields.'; return
        try:
            a = int(age); w = float(wt); h = float(ht)
            assert 13 <= a <= 100 and 30 <= w <= 300 and 100 <= h <= 250
        except Exception:
            self.err.text = 'Please enter valid numbers.'; return

        uid = db.create_user(name, a, w, h, self._level, self._goal)
        App.get_running_app().set_user(uid)
        App.get_running_app().build_main_screens()
        self.sm.current = 'dashboard'


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class DashboardScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='dashboard', **kwargs)
        self.sm = sm; self.user_id = user_id
        self._build()

    def on_pre_enter(self): self._refresh()

    def _build(self):
        self.root = BoxLayout(orientation='vertical')
        bg(self.root, th.get('bg'), radius=0)
        self.root.add_widget(make_header('FitAI', 'Dashboard'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                                 spacing=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.root.add_widget(self.scroll)
        self.root.add_widget(BottomNav('dashboard', self.sm))
        self.add_widget(self.root)

    def _refresh(self):
        self.content.clear_widgets()
        user  = db.get_user(self.user_id)
        stats = db.get_stats(self.user_id)
        logs  = db.get_recent_logs(self.user_id, 5)
        plan  = db.get_latest_plan(self.user_id)

        if not user: return

        # Greeting
        self.content.add_widget(lbl(f'Hello, {user["name"]}', size=20, bold=True, height=dp(30)))
        self.content.add_widget(lbl(
            f'{user["goal"].replace("_"," ").title()}  ·  {user["fitness_level"].capitalize()}',
            size=12, color=th.get('text2'), height=dp(20)
        ))

        # Today's workout card
        today_day = __import__('datetime').datetime.now().strftime('%A')
        today_workout = None
        if plan:
            for d in plan.get('weekly_plan', []):
                if d['day'] == today_day:
                    today_workout = d
                    break

        today_card = card()
        if today_workout:
            if today_workout['is_rest']:
                today_card.add_widget(lbl('Today — Rest & Recovery', size=14, bold=True, height=dp(22)))
                today_card.add_widget(lbl('Active recovery day. Focus on mobility and sleep.',
                                          size=12, color=th.get('text2'), height=dp(20)))
            else:
                today_card.add_widget(lbl(f'Today — {today_workout["focus"]}',
                                          size=14, bold=True, height=dp(22)))
                today_card.add_widget(lbl(f'{len(today_workout["exercises"])} exercises planned',
                                          size=12, color=th.get('text2'), height=dp(20)))
                start = primary_btn('Start Workout', height=dp(42),
                                    on_press=lambda *_: self._start_today(today_workout))
                today_card.add_widget(start)
        else:
            today_card.add_widget(lbl('No plan yet', size=14, bold=True, height=dp(22)))
            today_card.add_widget(lbl('Go to Plan to generate your AI workout plan.',
                                      size=12, color=th.get('text2'), height=dp(20)))
            gen = primary_btn('Generate Plan', height=dp(42),
                              on_press=lambda *_: setattr(self.sm, 'current', 'plan'))
            today_card.add_widget(gen)
        self.content.add_widget(today_card)

        # Stat grid
        stat_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(120))
        for val, label, color in [
            (stats['total_sessions'],             'Sessions',     th.get('blue')),
            (f"{stats['total_volume_kg']:,.0f}",  'Volume (kg)',  th.get('green')),
            (stats['avg_rpe'] or '—',             'Avg RPE',      th.get('amber')),
            (stats['unique_exercises'],            'Exercises',    th.get('purple')),
        ]:
            sc = card()
            sc.add_widget(lbl(str(val), size=22, color=color, bold=True,
                              halign='center', height=dp(32)))
            sc.add_widget(lbl(label, size=10, color=th.get('text2'),
                              halign='center', height=dp(16)))
            stat_grid.add_widget(sc)
        self.content.add_widget(stat_grid)

        # Recent activity
        self.content.add_widget(section_hdr('Recent Activity'))
        if not logs:
            self.content.add_widget(lbl('No sessions logged yet.',
                                        size=12, color=th.get('text3'), height=dp(20)))
        else:
            for log in logs:
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36),
                                padding=[dp(12), 0])
                bg(row, th.get('surface'), radius=dp(6))
                row.add_widget(lbl(log['exercise_name'], size=13, height=dp(36)))
                detail = f"{log['sets']}x{log['reps']}"
                if log['weight_kg'] > 0: detail += f" @ {log['weight_kg']}kg"
                if log.get('rpe'):       detail += f"  RPE {log['rpe']}"
                row.add_widget(lbl(detail, size=11, color=th.get('text2'),
                                   halign='right', height=dp(36)))
                self.content.add_widget(row)

        self.content.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

    def _start_today(self, day_data):
        App.get_running_app().active_day = day_data
        self.sm.current = 'workout'


# ─────────────────────────────────────────────────────────────────────────────
#  PLAN SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class PlanScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='plan', **kwargs)
        self.sm = sm; self.user_id = user_id
        self.days = 4
        self._dbtns = {}
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        bg(root, th.get('bg'), radius=0)
        root.add_widget(make_header('Plan', 'AI-Generated Weekly Program'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                                 spacing=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))

        # Days selector
        self.content.add_widget(section_hdr('Training Days per Week'))
        drow = BoxLayout(orientation='horizontal', spacing=dp(6),
                         size_hint_y=None, height=dp(38))
        for d in [2, 3, 4, 5, 6]:
            b = Button(text=str(d), font_size=sp(13), bold=d == self.days,
                       size_hint=(1, 1),
                       background_color=CLEAR, background_normal='',
                       color=th.get('blue') if d == self.days else th.get('text2'))
            bg(b, th.get('blue_dim') if d == self.days else th.get('surface'), radius=dp(8))
            border(b, th.get('blue') if d == self.days else th.get('border'), radius=dp(8))
            b.bind(on_press=lambda bt, day=d: self._set_days(day))
            self._dbtns[d] = b
            drow.add_widget(b)
        self.content.add_widget(drow)

        self.gen_btn = primary_btn('Generate Plan', on_press=self._generate)
        self.content.add_widget(self.gen_btn)

        self.status = lbl('', size=12, color=th.get('text2'), halign='center', height=dp(20))
        self.content.add_widget(self.status)

        self.plan_area = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.plan_area.bind(minimum_height=self.plan_area.setter('height'))
        self.content.add_widget(self.plan_area)

        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        root.add_widget(BottomNav('plan', self.sm))
        self.add_widget(root)

        # Load saved plan on first build
        Clock.schedule_once(self._load_saved, 0.1)

    def on_pre_enter(self):
        pass  # Plan persists — no reload needed

    def _load_saved(self, *_):
        plan = db.get_latest_plan(self.user_id)
        if plan:
            self._render_plan(plan)
            self.gen_btn.text = 'Regenerate Plan'

    def _set_days(self, d):
        self.days = d
        for day, btn in self._dbtns.items():
            active = day == d
            btn.bold  = active
            btn.color = th.get('blue') if active else th.get('text2')
            btn.canvas.before.clear()
            bg(btn, th.get('blue_dim') if active else th.get('surface'), radius=dp(8))
            btn.canvas.after.clear()
            border(btn, th.get('blue') if active else th.get('border'), radius=dp(8))

    def _generate(self, *_):
        self.gen_btn.text     = 'Generating...'
        self.gen_btn.disabled = True
        Clock.schedule_once(self._do_generate, 0.15)

    def _do_generate(self, *_):
        user    = db.get_user(self.user_id)
        history = db.get_logs(self.user_id)
        plan    = rec.generate(user, history, self.days)
        db.save_plan(self.user_id, plan)
        self._render_plan(plan)
        self.gen_btn.text     = 'Regenerate Plan'
        self.gen_btn.disabled = False

    def _render_plan(self, plan):
        self.plan_area.clear_widgets()

        # ML strip
        intensity = plan.get('intensity', 'moderate_intensity').replace('_', ' ').title()
        conf      = plan.get('confidence', 0)

        strip = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32),
                          padding=[dp(8), 0], spacing=dp(8))
        bg(strip, th.get('blue_dim'), radius=dp(8))
        strip.add_widget(lbl(f'ML: {intensity}', size=11, color=th.get('blue'), height=dp(32)))
        strip.add_widget(lbl(f'Confidence: {conf}%', size=11, color=th.get('text2'),
                             halign='right', height=dp(32)))
        self.plan_area.add_widget(strip)

        if plan.get('ml_note'):
            self.plan_area.add_widget(lbl(plan['ml_note'], size=11,
                                          color=th.get('text2'), height=dp(32)))

        # Weekly plan
        for day in plan.get('weekly_plan', []):
            day_card = card()

            hdr_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(26))
            day_color = th.get('text3') if day['is_rest'] else th.get('blue')
            hdr_row.add_widget(lbl(day['day'], size=13, bold=True, color=day_color, height=dp(26)))
            hdr_row.add_widget(lbl(day['focus'], size=12, color=th.get('text2'),
                                   halign='right', height=dp(26)))
            day_card.add_widget(hdr_row)

            if day['is_rest']:
                day_card.add_widget(lbl('Recovery Day — rest, hydrate, sleep well.',
                                        size=11, color=th.get('text3'), height=dp(20)))
            else:
                for ex in day.get('exercises', []):
                    ex_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(38),
                                       padding=[0, dp(4)])
                    ex_row.add_widget(lbl(ex['name'], size=12, height=dp(38)))
                    detail = f"{ex['sets']}x{ex['reps']}"
                    if ex.get('suggested_weight_kg', 0) > 0:
                        detail += f"  {ex['suggested_weight_kg']}kg"
                    ex_row.add_widget(lbl(detail, size=11, color=th.get('blue'),
                                          halign='right', height=dp(38)))
                    day_card.add_widget(ex_row)

                # Start Workout button
                start = Button(
                    text='Start Workout', font_size=sp(12), bold=True,
                    size_hint=(1, None), height=dp(36),
                    background_color=CLEAR, background_normal='',
                    color=th.get('blue'),
                )
                bg(start, th.get('blue_dim'), radius=dp(8))
                border(start, th.get('blue'), radius=dp(8))
                day_data = dict(day)
                start.bind(on_press=lambda b, d=day_data: self._start(d))
                day_card.add_widget(start)

            self.plan_area.add_widget(day_card)

        # Tips
        self.plan_area.add_widget(section_hdr('Coaching Notes'))
        tips_card = card()
        for tip in plan.get('tips', []):
            tips_card.add_widget(lbl(f'— {tip}', size=11, color=th.get('text2'), height=dp(28)))
        self.plan_area.add_widget(tips_card)

    def _start(self, day_data):
        App.get_running_app().active_day = day_data
        self.sm.current = 'workout'


# ─────────────────────────────────────────────────────────────────────────────
#  ACTIVE WORKOUT SCREEN
# ─────────────────────────────────────────────────────────────────────────────

EXERCISES = [
    'Barbell Bench Press','Incline Dumbbell Press','Push-Up','Dumbbell Chest Press',
    'Pull-Up','Barbell Row','Lat Pulldown','Seated Cable Row','Deadlift',
    'Barbell Squat','Romanian Deadlift','Leg Press','Lunges','Bulgarian Split Squat',
    'Barbell Overhead Press','Dumbbell Lateral Raise','Arnold Press','Face Pull',
    'Barbell Curl','Dumbbell Bicep Curl','Tricep Pushdown','Skull Crusher',
    'Plank','Ab Wheel Rollout','Hanging Leg Raise','Crunches',
]


class WorkoutScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='workout', **kwargs)
        self.sm = sm; self.user_id = user_id
        self.entries = []
        self._build()

    def on_pre_enter(self):
        day = App.get_running_app().active_day
        if day:
            self.entries = [
                {'name': ex['name'], 'sets': str(ex['sets']),
                 'reps': ex['reps'].split('-')[0] if '-' in str(ex['reps']) else str(ex['reps']),
                 'weight': str(ex.get('suggested_weight_kg', 0)) if ex.get('suggested_weight_kg', 0) > 0 else '',
                 'rpe': '', 'done': False}
                for ex in day.get('exercises', [])
            ]
        self._refresh()

    def _build(self):
        self.root_layout = BoxLayout(orientation='vertical')
        bg(self.root_layout, th.get('bg'), radius=0)
        self.header = make_header('Active Workout', 'Complete each exercise and log your session')
        self.root_layout.add_widget(self.header)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(10), PAD, dp(10)],
                                 spacing=dp(10), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.root_layout.add_widget(self.scroll)
        self.root_layout.add_widget(BottomNav('workout', self.sm))
        self.add_widget(self.root_layout)

    def _refresh(self):
        self.content.clear_widgets()

        if not self.entries:
            self.content.add_widget(lbl('No exercises loaded.', size=13,
                                        color=th.get('text2'), height=dp(30)))
            self.content.add_widget(lbl('Go to Plan, open a day and tap Start Workout.',
                                        size=12, color=th.get('text3'), height=dp(20)))
        else:
            done_count = sum(1 for e in self.entries if e['done'])
            # Progress bar
            prog_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                                 height=dp(24), spacing=dp(8))
            prog_row.add_widget(lbl(f'{done_count}/{len(self.entries)} done',
                                    size=11, color=th.get('text2'), height=dp(24)))
            prog_wrap = BoxLayout(size_hint=(1, None), height=dp(6),
                                  pos_hint={'center_y': 0.5})
            with prog_wrap.canvas:
                Color(rgba=th.get('border'))
                prog_wrap._bg = Rectangle(pos=prog_wrap.pos, size=prog_wrap.size)
                Color(rgba=th.get('blue'))
                pct = done_count / max(len(self.entries), 1)
                prog_wrap._fill = Rectangle(pos=prog_wrap.pos,
                                            size=(prog_wrap.width * pct, prog_wrap.height))
            prog_wrap.bind(
                pos=lambda w, v: (setattr(w._bg, 'pos', v), setattr(w._fill, 'pos', v)),
                size=lambda w, v: (setattr(w._bg, 'size', v),
                                   setattr(w._fill, 'size',
                                           (v[0] * done_count / max(len(self.entries), 1), v[1]))),
            )
            prog_row.add_widget(prog_wrap)
            self.content.add_widget(prog_row)

            for i, entry in enumerate(self.entries):
                self.content.add_widget(self._exercise_card(i, entry))

        # Add exercise manually
        self.content.add_widget(section_hdr('Add Exercise'))
        self.add_spinner = Spinner(
            text='Select exercise', values=EXERCISES,
            size_hint_y=None, height=dp(42),
            font_size=sp(13),
            background_color=th.get('surface'),
            color=th.get('text'),
        )
        self.content.add_widget(self.add_spinner)
        add_btn = secondary_btn('Add to Session', on_press=self._add_manual)
        self.content.add_widget(add_btn)

        # Status + complete
        self.status_lbl = lbl('', size=12, color=th.get('green'),
                               halign='center', height=dp(24))
        self.content.add_widget(self.status_lbl)

        if self.entries:
            done_count = sum(1 for e in self.entries if e['done'])
            self.complete_btn = primary_btn(
                f'Complete Session ({done_count} exercises)',
                on_press=self._complete
            )
            self.complete_btn.disabled = done_count == 0
            self.content.add_widget(self.complete_btn)

    def _exercise_card(self, idx, entry):
        c = card()
        done_col = th.get('text3') if entry['done'] else th.get('text')
        c.add_widget(lbl(entry['name'], size=14, bold=True, color=done_col, height=dp(24)))

        # Sets / Reps / Weight inputs
        irow = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(70))
        for field, label, hint in [('sets','Sets','3'),('reps','Reps','10'),('weight','Wt (kg)','0')]:
            col = BoxLayout(orientation='vertical', spacing=dp(2))
            col.add_widget(section_hdr(label))
            i = TextInput(
                text=entry[field], hint_text=hint, multiline=False, input_type='number',
                font_size=sp(13), size_hint_y=None, height=dp(40),
                background_color=th.get('surface'),
                foreground_color=th.get('text'),
                hint_text_color=th.get('text3'),
                cursor_color=th.get('blue'),
                padding=[dp(8), dp(8)],
            )
            field_copy = field
            i.bind(text=lambda w, v, f=field_copy, i=idx: self._update(i, f, v))
            col.add_widget(i)
            irow.add_widget(col)
        c.add_widget(irow)

        # RPE
        c.add_widget(section_hdr('RPE'))
        rpe_row = BoxLayout(orientation='horizontal', spacing=dp(4),
                            size_hint_y=None, height=dp(34))
        for n in range(1, 11):
            active = entry['rpe'] == str(n)
            b = Button(
                text=str(n), font_size=sp(11), bold=active,
                size_hint=(1, 1),
                background_color=CLEAR, background_normal='',
                color=th.get('blue') if active else th.get('text3'),
            )
            bg(b, th.get('blue_dim') if active else th.get('surface'), radius=dp(6))
            border(b, th.get('blue') if active else th.get('border'), radius=dp(6))
            b.bind(on_press=lambda bt, v=n, i=idx: self._set_rpe(i, v))
            rpe_row.add_widget(b)
        c.add_widget(rpe_row)

        # Done toggle
        done_btn = Button(
            text='Mark Done' if not entry['done'] else 'Done',
            font_size=sp(12), bold=entry['done'],
            size_hint=(1, None), height=dp(36),
            background_color=CLEAR, background_normal='',
            color=th.get('green') if entry['done'] else th.get('text2'),
        )
        done_col_bg = th.get('green_dim') if entry['done'] else th.get('surface')
        bg(done_btn, done_col_bg, radius=dp(8))
        border(done_btn,
               th.get('green') if entry['done'] else th.get('border'), radius=dp(8))
        done_btn.bind(on_press=lambda bt, i=idx: self._toggle_done(i))
        c.add_widget(done_btn)
        return c

    def _update(self, idx, field, val):
        if idx < len(self.entries):
            self.entries[idx][field] = val

    def _set_rpe(self, idx, val):
        if idx < len(self.entries):
            self.entries[idx]['rpe'] = str(val)
        self._refresh()

    def _toggle_done(self, idx):
        if idx < len(self.entries):
            self.entries[idx]['done'] = not self.entries[idx]['done']
        self._refresh()

    def _add_manual(self, *_):
        ex = self.add_spinner.text
        if ex and ex != 'Select exercise':
            self.entries.append({'name': ex, 'sets': '3', 'reps': '10',
                                 'weight': '', 'rpe': '', 'done': False})
            self._refresh()

    def _complete(self, *_):
        to_log = [e for e in self.entries if e['done']]
        if not to_log:
            self.status_lbl.text = 'Mark at least one exercise as done.'; return

        for e in to_log:
            try:
                db.log_workout(
                    user_id       = self.user_id,
                    exercise_name = e['name'],
                    sets          = int(e['sets'] or 1),
                    reps          = int(e['reps'] or 1),
                    weight_kg     = float(e['weight'] or 0),
                    rpe           = float(e['rpe']) if e['rpe'] else None,
                )
            except Exception:
                pass

        self.status_lbl.color = th.get('green')
        self.status_lbl.text  = f'Session saved — {len(to_log)} exercises logged.'
        self.entries = []
        App.get_running_app().active_day = None
        Clock.schedule_once(lambda *_: setattr(self.sm, 'current', 'dashboard'), 1.5)


# ─────────────────────────────────────────────────────────────────────────────
#  STATS SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class StatsScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='stats', **kwargs)
        self.sm = sm; self.user_id = user_id
        self._build()

    def on_pre_enter(self): self._refresh()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        bg(root, th.get('bg'), radius=0)
        root.add_widget(make_header('Statistics', 'Training analytics and history'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                                 spacing=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        root.add_widget(BottomNav('stats', self.sm))
        self.add_widget(root)

    def _refresh(self):
        self.content.clear_widgets()
        stats = db.get_stats(self.user_id)
        logs  = db.get_recent_logs(self.user_id, 30)

        if stats['total_sessions'] == 0:
            self.content.add_widget(lbl('No workout data yet.', size=14,
                                        color=th.get('text2'), halign='center', height=dp(40)))
            return

        # Summary
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(120))
        for val, label, col in [
            (stats['total_sessions'],           'Sessions',    th.get('blue')),
            (f"{stats['total_volume_kg']:,.0f}",'Volume kg',   th.get('green')),
            (stats['avg_rpe'] or '—',           'Avg RPE',     th.get('amber')),
            (stats['unique_exercises'],          'Exercises',   th.get('purple')),
        ]:
            sc = card()
            sc.add_widget(lbl(str(val), size=22, color=col, bold=True,
                              halign='center', height=dp(32)))
            sc.add_widget(lbl(label, size=10, color=th.get('text2'),
                              halign='center', height=dp(16)))
            grid.add_widget(sc)
        self.content.add_widget(grid)

        # RPE bar chart
        rpe_logs = [l for l in reversed(logs) if l.get('rpe')][-12:]
        if len(rpe_logs) >= 2:
            self.content.add_widget(section_hdr('RPE Trend'))
            chart_card = card(height=dp(130))
            chart_inner = BoxLayout(orientation='horizontal', spacing=dp(4),
                                    size_hint=(1, 1))
            for log in rpe_logs:
                rpe = log['rpe']
                col_c = card()
                col_c = BoxLayout(orientation='vertical', spacing=dp(2))
                val_l = lbl(str(rpe), size=9, color=th.get('text2'),
                            halign='center', height=dp(16))
                bar_wrap = BoxLayout(size_hint=(1, 1))
                fill_h = rpe / 10.0
                bar_outer = BoxLayout(orientation='vertical', size_hint=(1, 1))
                spacer = BoxLayout(size_hint=(1, 1 - fill_h))
                fill = BoxLayout(size_hint=(1, fill_h))
                fill_col = (th.get('green') if rpe <= 5 else
                            th.get('blue')  if rpe <= 7 else
                            th.get('amber') if rpe <= 8 else th.get('red'))
                bg(fill, fill_col, radius=dp(3))
                bar_outer.add_widget(spacer)
                bar_outer.add_widget(fill)
                bar_wrap.add_widget(bar_outer)
                ex_l = lbl(log['exercise_name'][:4], size=8, color=th.get('text3'),
                           halign='center', height=dp(14))
                col_c.add_widget(val_l)
                col_c.add_widget(bar_wrap)
                col_c.add_widget(ex_l)
                chart_inner.add_widget(col_c)
            chart_card.add_widget(chart_inner)
            self.content.add_widget(chart_card)

        # Log table
        self.content.add_widget(section_hdr('Recent Sessions'))
        hdr_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(24), padding=[dp(8), 0])
        bg(hdr_row, th.get('surface'), radius=dp(6))
        for label, sx in [('Exercise',1.8),('Sets',0.5),('Reps',0.5),('Wt',0.6),('RPE',0.5)]:
            h = lbl(label, size=10, color=th.get('text3'), bold=True,
                    halign='center', height=dp(24))
            h.size_hint_x = sx
            hdr_row.add_widget(h)
        self.content.add_widget(hdr_row)

        for i, log in enumerate(logs[:20]):
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(32), padding=[dp(8), 0])
            bg(row, th.get('surface') if i % 2 == 0 else th.get('bg'), radius=0)
            for val, sx in [
                (log['exercise_name'][:18], 1.8),
                (str(log['sets']),          0.5),
                (str(log['reps']),          0.5),
                (str(log['weight_kg']),     0.6),
                (str(log.get('rpe') or '—'),0.5),
            ]:
                l = lbl(val, size=11, color=th.get('text'), halign='center', height=dp(32))
                l.size_hint_x = sx
                row.add_widget(l)
            self.content.add_widget(row)

        self.content.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))


# ─────────────────────────────────────────────────────────────────────────────
#  AI INSIGHTS SCREEN  (6th screen)
# ─────────────────────────────────────────────────────────────────────────────

class InsightsScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='insights', **kwargs)
        self.sm = sm; self.user_id = user_id
        self._build()

    def on_pre_enter(self): self._refresh()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        bg(root, th.get('bg'), radius=0)
        root.add_widget(make_header('AI Insights', 'How the system learns and adapts'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                                 spacing=dp(14), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        root.add_widget(BottomNav('insights', self.sm))
        self.add_widget(root)

    def _refresh(self):
        self.content.clear_widgets()
        user    = db.get_user(self.user_id)
        history = db.get_logs(self.user_id)

        if not user:
            return

        plan = db.get_latest_plan(self.user_id)
        days = 4
        if plan:
            training_days = [d for d in plan.get('weekly_plan', []) if not d.get('is_rest')]
            days = max(2, len(training_days))

        insights = rec.get_ai_insights(user, history, days)
        ml       = insights['ml']
        rules    = insights['rules']
        adapt    = insights['adaptation']
        overload = insights['overload']

        # ── SECTION 1: ML Model Status ────────────────────────────────────────
        self.content.add_widget(self._section_title('Machine Learning Model', th.get('blue')))
        ml_card = card()

        # Data points + confidence bar
        dp_count = ml['data_points']
        conf     = ml['confidence']

        ml_card.add_widget(lbl(f'Training data collected: {dp_count} sessions',
                               size=13, height=dp(22)))

        # Confidence bar
        ml_card.add_widget(lbl('Model Confidence', size=11, color=th.get('text2'), height=dp(18)))
        conf_wrap = BoxLayout(size_hint=(1, None), height=dp(10))
        with conf_wrap.canvas:
            Color(rgba=th.get('border'))
            conf_wrap._bg = Rectangle(pos=conf_wrap.pos, size=conf_wrap.size)
            Color(rgba=th.get('blue'))
            conf_wrap._fill = Rectangle(pos=conf_wrap.pos,
                                        size=(0, conf_wrap.height))
        def update_conf(w, v):
            w._bg.pos   = v[0], v[1] if hasattr(v, '__len__') else w.pos
            w._bg.size  = w.size
            w._fill.pos = w.pos
            w._fill.size = (w.width * conf / 100, w.height)
        conf_wrap.bind(pos=lambda w, v: update_conf(w, v),
                       size=lambda w, v: update_conf(w, v))
        ml_card.add_widget(conf_wrap)
        ml_card.add_widget(lbl(f'{conf}% confident', size=11, color=th.get('blue'), height=dp(18)))

        # Intensity + RPE
        intensity_col = (th.get('amber')  if ml['intensity'] == 'low_intensity' else
                         th.get('blue')   if ml['intensity'] == 'moderate_intensity' else
                         th.get('red'))
        ml_card.add_widget(lbl(
            f"Predicted Intensity: {ml['intensity'].replace('_',' ').title()}",
            size=13, color=intensity_col, bold=True, height=dp(22)
        ))
        ml_card.add_widget(lbl(f"Avg RPE (last 10): {ml['avg_rpe']}", size=12,
                               color=th.get('text2'), height=dp(20)))

        trend = ml.get('rpe_trend', 'stable')
        trend_col = (th.get('red') if trend == 'rising' else
                     th.get('green') if trend == 'falling' else th.get('blue'))
        ml_card.add_widget(lbl(f"RPE Trend: {trend.title()}", size=12,
                               color=trend_col, height=dp(20)))
        ml_card.add_widget(lbl(f"Training weeks detected: {ml['weeks_active']}",
                               size=12, color=th.get('text2'), height=dp(20)))
        ml_card.add_widget(divider())
        ml_card.add_widget(lbl(ml['ml_note'], size=11, color=th.get('text2'), height=dp(36)))

        if dp_count < 5:
            ml_card.add_widget(lbl(
                f'Log {5 - dp_count} more sessions to enable personal ML retraining.',
                size=11, color=th.get('amber'), height=dp(22)
            ))

        self.content.add_widget(ml_card)

        # ── SECTION 2: Rule-Based System ──────────────────────────────────────
        self.content.add_widget(self._section_title('Rule-Based System', th.get('green')))
        rules_card = card()

        rules_card.add_widget(lbl('Active Safety Rules', size=13, bold=True, height=dp(22)))

        for rule_name in [rules['recovery_rule'], rules['overload_rule']]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24),
                            spacing=dp(8))
            dot = BoxLayout(size_hint=(None, None), size=(dp(8), dp(8)),
                            pos_hint={'center_y': 0.5})
            bg(dot, th.get('green'), radius=dp(4))
            row.add_widget(dot)
            row.add_widget(lbl(rule_name, size=11, color=th.get('text2'), height=dp(24)))
            rules_card.add_widget(row)

        rules_card.add_widget(divider())

        # Volume prescription
        vol = rules['volume_prescription']
        rules_card.add_widget(lbl('Current Volume Prescription', size=13,
                                  bold=True, height=dp(22)))
        rules_card.add_widget(lbl(
            f"Sets: {vol['sets']}  ·  Reps: {vol['reps']}  ·  Rest: {vol['rest_sec']}s",
            size=12, color=th.get('blue'), height=dp(20)
        ))

        rules_card.add_widget(divider())

        # Muscle group recovery status
        rules_card.add_widget(lbl('Muscle Recovery Status', size=13, bold=True, height=dp(22)))
        all_groups = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core']
        recovering = rules.get('recovering_groups', [])
        for group in all_groups:
            is_resting = group in recovering
            status_col = th.get('red') if is_resting else th.get('green')
            status_txt = 'Recovering (48hr)' if is_resting else 'Ready to train'
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(26))
            row.add_widget(lbl(group.capitalize(), size=12, height=dp(26)))
            row.add_widget(lbl(status_txt, size=11, color=status_col,
                               halign='right', height=dp(26)))
            rules_card.add_widget(row)

        self.content.add_widget(rules_card)

        # ── SECTION 3: Progressive Overload ───────────────────────────────────
        if overload:
            self.content.add_widget(self._section_title('Progressive Overload', th.get('amber')))
            ov_card = card()
            for ex_name, result in overload.items():
                ov_card.add_widget(lbl(ex_name, size=12, bold=True, height=dp(20)))
                col = th.get('green') if result['ready'] else th.get('text3')
                ov_card.add_widget(lbl(result['message'], size=11, color=col, height=dp(20)))
                ov_card.add_widget(divider())
            self.content.add_widget(ov_card)

        # ── SECTION 4: Adaptation History ─────────────────────────────────────
        self.content.add_widget(self._section_title('Adaptation History', th.get('purple')))
        hist_card = card()

        if not adapt:
            hist_card.add_widget(lbl(
                'Adaptation history will appear here after 5+ logged sessions.\n'
                'The graph will show how the ML model\'s intensity prediction\n'
                'changes as it learns from your RPE patterns.',
                size=12, color=th.get('text2'), height=dp(60)
            ))
        else:
            hist_card.add_widget(lbl('Week-by-week intensity prediction',
                                     size=11, color=th.get('text2'), height=dp(18)))
            for entry in adapt:
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28))
                row.add_widget(lbl(f'Week {entry["week"]}', size=12,
                                   color=th.get('text2'), height=dp(28)))

                col = (th.get('amber') if entry['intensity'] == 'Low' else
                       th.get('blue')  if entry['intensity'] == 'Moderate' else
                       th.get('red'))
                row.add_widget(lbl(entry['intensity'], size=12, color=col,
                                   halign='center', height=dp(28)))
                row.add_widget(lbl(f'RPE {entry["avg_rpe"]}', size=11,
                                   color=th.get('text3'), halign='right', height=dp(28)))
                hist_card.add_widget(row)

            hist_card.add_widget(divider())
            hist_card.add_widget(lbl(
                'As your sessions accumulate, the model refines its predictions.\n'
                'Consistent RPE logging improves recommendation accuracy.',
                size=11, color=th.get('text2'), height=dp(40)
            ))

        self.content.add_widget(hist_card)
        self.content.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

    def _section_title(self, text, color):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(8))
        dot = BoxLayout(size_hint=(None, None), size=(dp(10), dp(10)),
                        pos_hint={'center_y': 0.5})
        bg(dot, color, radius=dp(5))
        row.add_widget(dot)
        row.add_widget(lbl(text, size=14, bold=True, color=th.get('text'), height=dp(28)))
        return row


# ─────────────────────────────────────────────────────────────────────────────
#  PROFILE / THEME TOGGLE SCREEN  (accessible from dashboard header)
# ─────────────────────────────────────────────────────────────────────────────

class ProfileScreen(Screen):
    def __init__(self, sm, user_id, **kwargs):
        super().__init__(name='profile', **kwargs)
        self.sm = sm; self.user_id = user_id
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        bg(root, th.get('bg'), radius=0)
        root.add_widget(make_header('Profile', 'Settings and preferences'))

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                            spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        user = db.get_user(self.user_id)
        if user:
            c = card()
            for label, val in [
                ('Name',   user['name']),
                ('Goal',   user['goal'].replace('_', ' ').title()),
                ('Level',  user['fitness_level'].capitalize()),
                ('Age',    f"{user['age']} years"),
                ('Weight', f"{user['weight_kg']} kg"),
                ('Height', f"{user['height_cm']} cm"),
            ]:
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28))
                row.add_widget(lbl(label, size=13, color=th.get('text2'), height=dp(28)))
                row.add_widget(lbl(val, size=13, halign='right', height=dp(28)))
                c.add_widget(row)
            content.add_widget(c)

        # Theme toggle
        content.add_widget(section_hdr('Appearance'))
        theme_row = BoxLayout(orientation='horizontal', spacing=dp(10),
                              size_hint_y=None, height=dp(44))
        for mode in ['light', 'dark']:
            active = th.current() == mode
            b = Button(
                text=f'{mode.capitalize()} Mode',
                font_size=sp(13), bold=active,
                size_hint=(1, 1),
                background_color=CLEAR, background_normal='',
                color=th.get('blue') if active else th.get('text2'),
            )
            bg(b, th.get('blue_dim') if active else th.get('surface'), radius=dp(8))
            border(b, th.get('blue') if active else th.get('border'), radius=dp(8))
            b.bind(on_press=lambda bt, m=mode: App.get_running_app().set_theme(m))
            theme_row.add_widget(b)
        content.add_widget(theme_row)

        # Switch profile
        content.add_widget(section_hdr('Account'))
        switch_btn = secondary_btn('Switch Profile',
                                   on_press=lambda *_: setattr(self.sm, 'current', 'select_profile'))
        content.add_widget(switch_btn)

        back_btn = primary_btn('Back to Dashboard',
                               on_press=lambda *_: setattr(self.sm, 'current', 'dashboard'))
        content.add_widget(back_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)


# ─────────────────────────────────────────────────────────────────────────────
#  SELECT PROFILE SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class SelectProfileScreen(Screen):
    def __init__(self, sm, **kwargs):
        super().__init__(name='select_profile', **kwargs)
        self.sm = sm
        self._build()

    def on_pre_enter(self): self._refresh()

    def _build(self):
        self.root_layout = BoxLayout(orientation='vertical')
        bg(self.root_layout, th.get('bg'), radius=0)
        self.root_layout.add_widget(make_header('Switch Profile', 'Select or create a profile'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', padding=[PAD, dp(12), PAD, dp(12)],
                                 spacing=dp(10), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.root_layout.add_widget(self.scroll)
        self.add_widget(self.root_layout)

    def _refresh(self):
        self.content.clear_widgets()
        users = db.get_all_users()
        current_uid = App.get_running_app().user_id

        self.content.add_widget(section_hdr('Existing Profiles'))
        for user in users:
            is_active = user['id'] == current_uid
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(56), padding=[dp(12), dp(6)], spacing=dp(10))
            bg(row, th.get('blue_dim') if is_active else th.get('card'), radius=RAD)
            border(row, th.get('blue') if is_active else th.get('border'), radius=RAD)

            info = BoxLayout(orientation='vertical')
            info.add_widget(lbl(user['name'], size=14, bold=True, height=dp(22)))
            info.add_widget(lbl(
                f"{user['fitness_level'].capitalize()}  ·  {user['goal'].replace('_',' ').title()}",
                size=11, color=th.get('text2'), height=dp(18)
            ))
            row.add_widget(info)

            if not is_active:
                sel = Button(
                    text='Select', font_size=sp(12), bold=True,
                    size_hint=(None, None), size=(dp(70), dp(32)),
                    background_color=CLEAR, background_normal='',
                    color=th.get('blue'),
                )
                bg(sel, th.get('blue_dim'), radius=dp(8))
                uid = user['id']
                sel.bind(on_press=lambda b, u=uid: self._select(u))
                row.add_widget(sel)
            else:
                row.add_widget(lbl('Active', size=11, color=th.get('green'),
                                   halign='right', height=dp(32)))

            self.content.add_widget(row)

        self.content.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))
        self.content.add_widget(section_hdr('Create New'))
        new_btn = primary_btn('Create New Profile',
                              on_press=lambda *_: setattr(self.sm, 'current', 'setup'))
        self.content.add_widget(new_btn)

        back = secondary_btn('Back', on_press=lambda *_: setattr(self.sm, 'current', 'dashboard'))
        self.content.add_widget(back)

    def _select(self, uid):
        App.get_running_app().set_user(uid)
        App.get_running_app().build_main_screens()
        self.sm.current = 'dashboard'


# ─────────────────────────────────────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────────────────────────────────────

class FitAIApp(App):
    title    = 'FitAI'
    user_id  = None
    active_day = None

    def build(self):
        db.create_tables()
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))

        users = db.get_all_users()
        if users:
            self.set_user(users[0]['id'])
            self.build_main_screens()
            self.sm.current = 'dashboard'
        else:
            self.sm.add_widget(SetupScreen(self.sm))
            self.sm.current = 'setup'

        return self.sm

    def set_user(self, uid):
        self.user_id = uid

    def set_theme(self, mode):
        th.set_theme(mode)
        # Rebuild all screens with new theme
        self.build_main_screens()
        self.sm.current = 'dashboard'

    def build_main_screens(self):
        uid = self.user_id
        for name in ['dashboard','plan','workout','stats','insights','profile','select_profile']:
            if self.sm.has_screen(name):
                self.sm.remove_widget(self.sm.get_screen(name))

        self.sm.add_widget(DashboardScreen(self.sm, uid))
        self.sm.add_widget(PlanScreen(self.sm, uid))
        self.sm.add_widget(WorkoutScreen(self.sm, uid))
        self.sm.add_widget(StatsScreen(self.sm, uid))
        self.sm.add_widget(InsightsScreen(self.sm, uid))
        self.sm.add_widget(ProfileScreen(self.sm, uid))
        self.sm.add_widget(SelectProfileScreen(self.sm))


if __name__ == '__main__':
    FitAIApp().run()
