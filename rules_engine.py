"""
rules_engine.py — Rule-Based System.
Enforces exercise science as hard rules.
Every split includes rest days distributed for optimal recovery.
"""

from datetime import datetime, timedelta

EXERCISE_LIBRARY = {
    'chest': {
        'beginner':     ['Push-Up', 'Dumbbell Chest Press', 'Incline Push-Up'],
        'intermediate': ['Barbell Bench Press', 'Incline Dumbbell Press', 'Cable Fly'],
        'advanced':     ['Weighted Dips', 'Decline Barbell Press', 'Incline Cable Fly'],
    },
    'back': {
        'beginner':     ['Lat Pulldown', 'Seated Cable Row', 'Dumbbell Row'],
        'intermediate': ['Pull-Up', 'Barbell Row', 'T-Bar Row'],
        'advanced':     ['Weighted Pull-Up', 'Pendlay Row', 'Deadlift'],
    },
    'legs': {
        'beginner':     ['Bodyweight Squat', 'Leg Press', 'Leg Curl'],
        'intermediate': ['Barbell Squat', 'Romanian Deadlift', 'Lunges'],
        'advanced':     ['Front Squat', 'Bulgarian Split Squat', 'Hack Squat'],
    },
    'shoulders': {
        'beginner':     ['Dumbbell Lateral Raise', 'Front Raise', 'Machine Shoulder Press'],
        'intermediate': ['Barbell Overhead Press', 'Arnold Press', 'Face Pull'],
        'advanced':     ['Push Press', 'Cable Lateral Raise', 'Behind-the-Neck Press'],
    },
    'arms': {
        'beginner':     ['Dumbbell Bicep Curl', 'Tricep Pushdown', 'Hammer Curl'],
        'intermediate': ['Barbell Curl', 'Skull Crusher', 'Preacher Curl'],
        'advanced':     ['Incline Dumbbell Curl', 'Close-Grip Bench Press', 'Cable Curl'],
    },
    'core': {
        'beginner':     ['Plank', 'Crunches', 'Dead Bug'],
        'intermediate': ['Hanging Knee Raise', 'Ab Wheel Rollout', 'Russian Twist'],
        'advanced':     ['Dragon Flag', 'Hanging Leg Raise', 'Pallof Press'],
    },
}

VOLUME_RULES = {
    'muscle_gain': {
        'beginner':     {'sets': 3, 'reps': '8-12',  'rest_sec': 90},
        'intermediate': {'sets': 4, 'reps': '6-10',  'rest_sec': 120},
        'advanced':     {'sets': 5, 'reps': '4-8',   'rest_sec': 180},
    },
    'fat_loss': {
        'beginner':     {'sets': 3, 'reps': '12-15', 'rest_sec': 45},
        'intermediate': {'sets': 4, 'reps': '12-15', 'rest_sec': 45},
        'advanced':     {'sets': 4, 'reps': '15-20', 'rest_sec': 30},
    },
    'endurance': {
        'beginner':     {'sets': 2, 'reps': '15-20', 'rest_sec': 30},
        'intermediate': {'sets': 3, 'reps': '15-20', 'rest_sec': 30},
        'advanced':     {'sets': 3, 'reps': '20-25', 'rest_sec': 20},
    },
    'general_fitness': {
        'beginner':     {'sets': 3, 'reps': '10-12', 'rest_sec': 60},
        'intermediate': {'sets': 3, 'reps': '10-12', 'rest_sec': 60},
        'advanced':     {'sets': 4, 'reps': '8-12',  'rest_sec': 90},
    },
}

REST_TIPS = [
    'Prioritize 7-9 hours of sleep for muscle repair and hormone recovery.',
    'Stay hydrated — drink at least 2-3 liters of water today.',
    'Light walking or stretching promotes blood flow without taxing muscles.',
    'Use this day for mobility work — hip flexors, thoracic spine, shoulders.',
    'Eat adequate protein today (1.6-2.2g per kg) to support ongoing recovery.',
]

# Full 7-day week splits with rest days explicitly placed
SPLIT_TEMPLATES = {
    2: [
        {'day': 'Monday',    'focus': 'Full Body A', 'is_rest': False, 'groups': ['chest', 'back', 'legs', 'core']},
        {'day': 'Tuesday',   'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Wednesday', 'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Thursday',  'focus': 'Full Body B', 'is_rest': False, 'groups': ['shoulders', 'arms', 'legs', 'core']},
        {'day': 'Friday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Saturday',  'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Sunday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
    ],
    3: [
        {'day': 'Monday',    'focus': 'Push',        'is_rest': False, 'groups': ['chest', 'shoulders', 'arms']},
        {'day': 'Tuesday',   'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Wednesday', 'focus': 'Pull',        'is_rest': False, 'groups': ['back', 'arms']},
        {'day': 'Thursday',  'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Friday',    'focus': 'Legs & Core', 'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Saturday',  'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Sunday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
    ],
    4: [
        {'day': 'Monday',    'focus': 'Upper A',     'is_rest': False, 'groups': ['chest', 'back', 'core']},
        {'day': 'Tuesday',   'focus': 'Lower A',     'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Wednesday', 'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Thursday',  'focus': 'Upper B',     'is_rest': False, 'groups': ['shoulders', 'arms', 'core']},
        {'day': 'Friday',    'focus': 'Lower B',     'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Saturday',  'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Sunday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
    ],
    5: [
        {'day': 'Monday',    'focus': 'Chest',       'is_rest': False, 'groups': ['chest', 'core']},
        {'day': 'Tuesday',   'focus': 'Back',        'is_rest': False, 'groups': ['back', 'core']},
        {'day': 'Wednesday', 'focus': 'Shoulders',   'is_rest': False, 'groups': ['shoulders', 'arms']},
        {'day': 'Thursday',  'focus': 'Arms',        'is_rest': False, 'groups': ['arms', 'core']},
        {'day': 'Friday',    'focus': 'Legs',        'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Saturday',  'focus': 'Rest',        'is_rest': True,  'groups': []},
        {'day': 'Sunday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
    ],
    6: [
        {'day': 'Monday',    'focus': 'Push A',      'is_rest': False, 'groups': ['chest', 'shoulders']},
        {'day': 'Tuesday',   'focus': 'Pull A',      'is_rest': False, 'groups': ['back', 'arms']},
        {'day': 'Wednesday', 'focus': 'Legs A',      'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Thursday',  'focus': 'Push B',      'is_rest': False, 'groups': ['chest', 'arms']},
        {'day': 'Friday',    'focus': 'Pull B',      'is_rest': False, 'groups': ['back', 'shoulders']},
        {'day': 'Saturday',  'focus': 'Legs B',      'is_rest': False, 'groups': ['legs', 'core']},
        {'day': 'Sunday',    'focus': 'Rest',        'is_rest': True,  'groups': []},
    ],
}

SAFETY_TIPS = {
    'muscle_gain':    [
        'Rest 48 hours before training the same muscle group again.',
        'Add 2.5 kg or 1-2 reps every 1-2 weeks for progressive overload.',
        'Eat in a calorie surplus of 200-300 kcal for muscle growth.',
        'Sleep 7-9 hours — recovery is when muscles grow.',
        'Always warm up with 50% of your working weight first.',
    ],
    'fat_loss':       [
        'Keep rest periods short (30-45 sec) to maintain heart rate.',
        'Combine resistance training with 150 min of cardio per week.',
        'Maintain a moderate calorie deficit of 300-500 kcal.',
        'Prioritize protein (1.6-2.2g per kg) to preserve muscle.',
        'Track workouts to maintain progressive overload while cutting.',
    ],
    'endurance':      [
        'Focus on time under tension with slow, controlled reps.',
        'Increase volume by no more than 10% per week.',
        'Stay hydrated before, during, and after training.',
        'Include zone 2 cardio at conversational pace 3x per week.',
        'Take a deload week every 4-6 weeks to prevent overtraining.',
    ],
    'general_fitness':[
        'Consistency beats intensity — showing up regularly matters most.',
        'Learn proper form first; add weight only when form is solid.',
        'Include mobility work in your warm-up and cool-down.',
        'Rest 1-2 days per week — recovery makes you stronger.',
        'Drink at least 2 liters of water daily.',
    ],
}

FORM_NOTES = {
    'Barbell Bench Press':    'Retract scapula; do not bounce bar off chest.',
    'Barbell Squat':          'Keep chest up, knees tracking over toes.',
    'Deadlift':               'Neutral spine throughout; engage lats before pulling.',
    'Pull-Up':                'Full extension at bottom; chin above bar at top.',
    'Push-Up':                'Core tight; lower chest to 2 cm from floor.',
    'Barbell Overhead Press': 'Brace core; avoid hyperextending lower back.',
    'Romanian Deadlift':      'Hinge at hips; feel hamstring stretch.',
    'Plank':                  'Squeeze glutes and abs; do not let hips sag.',
}


class RulesEngine:

    def generate_plan(self, user_id, fitness_level, goal, days_per_week,
                      workout_history=None):
        days_per_week = max(2, min(6, days_per_week))
        split  = SPLIT_TEMPLATES[days_per_week]
        volume = VOLUME_RULES[goal][fitness_level]
        avoid  = self._overtrained_groups(workout_history)

        weekly_plan = []
        for tpl in split:
            if tpl['is_rest']:
                weekly_plan.append({
                    'day':        tpl['day'],
                    'focus':      'Rest & Recovery',
                    'is_rest':    True,
                    'exercises':  [],
                    'rest_tips':  REST_TIPS,
                })
                continue

            exercises = []
            for group in tpl['groups']:
                if group in avoid:
                    continue
                options = EXERCISE_LIBRARY.get(group, {}).get(fitness_level, [])
                for ex in options[:2]:
                    exercises.append({
                        'name':         ex,
                        'sets':         volume['sets'],
                        'reps':         volume['reps'],
                        'rest_sec':     volume['rest_sec'],
                        'muscle_group': group,
                        'notes':        FORM_NOTES.get(ex),
                        'suggested_weight_kg': 0,
                        'weight_basis': '',
                    })

            weekly_plan.append({
                'day':       tpl['day'],
                'focus':     tpl['focus'],
                'is_rest':   False,
                'exercises': exercises,
            })

        return {
            'user_id':     user_id,
            'goal':        goal,
            'level':       fitness_level,
            'source':      'rules',
            'weekly_plan': weekly_plan,
            'tips':        SAFETY_TIPS[goal],
        }

    def check_overload(self, exercise_name, logs):
        if len(logs) < 4:
            return {'ready': False, 'message': 'Log more sessions to get overload suggestions.'}
        weights = [l.get('weight_kg', 0) for l in logs[-4:]]
        reps    = [l.get('reps', 0)      for l in logs[-4:]]
        if len(set(weights)) == 1 and len(set(reps)) == 1:
            return {
                'ready':   True,
                'message': f'Ready to progress on {exercise_name}. Try +2.5 kg or +2 reps.',
                'suggest': {'weight': weights[-1] + 2.5, 'reps': reps[-1] + 2},
            }
        return {'ready': False, 'message': 'Still adapting — maintain current load.'}

    def get_active_rules(self, user_id, fitness_level, goal, workout_history):
        """Returns a summary of which rules are currently active — for AI Insights screen."""
        avoid = self._overtrained_groups(workout_history)
        volume = VOLUME_RULES[goal][fitness_level]
        return {
            'recovering_groups': avoid,
            'ready_groups': [g for g in EXERCISE_LIBRARY if g not in avoid],
            'volume_prescription': volume,
            'recovery_rule': '48-hour muscle group recovery enforced',
            'overload_rule': 'Progressive overload checked after 4 consistent sessions',
        }

    def _overtrained_groups(self, history):
        if not history:
            return []
        threshold = datetime.utcnow() - timedelta(hours=48)
        recent = set()
        for log in history:
            try:
                dt = datetime.fromisoformat(str(log.get('date', '')))
            except Exception:
                continue
            if dt > threshold:
                name = log.get('exercise_name', '').lower()
                for group, levels in EXERCISE_LIBRARY.items():
                    for exs in levels.values():
                        if any(name in e.lower() for e in exs):
                            recent.add(group)
        return list(recent)
