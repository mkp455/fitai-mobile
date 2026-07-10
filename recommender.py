"""
recommender.py — Hybrid orchestrator.
Rules Engine generates safe base plan.
ML Model adjusts intensity without breaking safety rules.
"""

from rules_engine import RulesEngine
from ml_model import MLModel


class HybridRecommender:

    def __init__(self):
        self.rules = RulesEngine()
        self.ml    = MLModel()

    def generate(self, user_profile, history, days_per_week=4):
        uid   = user_profile['id']
        level = user_profile['fitness_level']
        goal  = user_profile['goal']

        # Step 1: Rules — safe base plan with rest days
        plan = self.rules.generate_plan(
            user_id         = uid,
            fitness_level   = level,
            goal            = goal,
            days_per_week   = days_per_week,
            workout_history = history,
        )

        # Step 2: ML — intensity prediction
        ml = self.ml.predict_intensity(user_profile, history, days_per_week)

        # Step 3: Apply ML adjustments to training days only
        adj = ml['adjustments']
        for day in plan['weekly_plan']:
            if day['is_rest']:
                continue
            for ex in day['exercises']:
                ex['sets'] = max(1, min(6, ex['sets'] + adj['sets_mod']))
                ex['reps'] = self._adjust_reps(ex['reps'], adj['reps_mod'])
                wt, basis  = self.ml.suggest_weight(ex['name'], history, user_profile)
                ex['suggested_weight_kg'] = wt
                ex['weight_basis']        = basis

        plan['source']     = 'hybrid'
        plan['intensity']  = ml['intensity']
        plan['confidence'] = ml['confidence']
        plan['ml_note']    = ml['ml_note']
        plan['ml_data']    = ml

        return plan

    def get_ai_insights(self, user_profile, history, days_per_week=4):
        """Full AI insights data for the dedicated insights screen."""
        ml_pred    = self.ml.predict_intensity(user_profile, history, days_per_week)
        rules_data = self.rules.get_active_rules(
            user_profile['id'],
            user_profile['fitness_level'],
            user_profile['goal'],
            history,
        )
        adapt_hist = self.ml.get_adaptation_history(history, days_per_week)

        # Per-exercise overload checks
        overload = {}
        ex_names = list({l['exercise_name'] for l in history})
        for ex in ex_names[:6]:
            ex_logs = [l for l in history if l.get('exercise_name') == ex]
            overload[ex] = self.rules.check_overload(ex, ex_logs)

        return {
            'ml':           ml_pred,
            'rules':        rules_data,
            'adaptation':   adapt_hist,
            'overload':     overload,
        }

    def _adjust_reps(self, reps_str, delta):
        if delta == 0:
            return reps_str
        try:
            if '-' in str(reps_str):
                lo, hi = map(int, str(reps_str).split('-'))
            else:
                lo = hi = int(reps_str)
            lo = max(1, lo + delta)
            hi = max(1, hi + delta)
            return f'{lo}-{hi}'
        except Exception:
            return reps_str
