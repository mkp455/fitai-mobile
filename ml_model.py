"""
ml_model.py — Machine Learning layer (numpy-only).
Predicts training intensity from RPE history.
Tracks adaptation history for the AI Insights screen.
"""

import numpy as np

FITNESS_SCORES = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
GOAL_SCORES    = {'muscle_gain': 0, 'fat_loss': 1, 'endurance': 2, 'general_fitness': 3}

ADJUSTMENTS = {
    'low_intensity':      {'sets_mod': -1, 'reps_mod': 2,  'weight_add': 0.0},
    'moderate_intensity': {'sets_mod':  0, 'reps_mod': 0,  'weight_add': 2.5},
    'high_intensity':     {'sets_mod': +1, 'reps_mod': -2, 'weight_add': 5.0},
}

LABELS = ['low_intensity', 'moderate_intensity', 'high_intensity']


class MLModel:

    def predict_intensity(self, user_profile, logs, days_per_week=3):
        avg_rpe      = self._avg_rpe(logs)
        weeks_active = len(logs) // max(days_per_week, 1)
        fitness_sc   = FITNESS_SCORES.get(user_profile.get('fitness_level', 'beginner'), 0)

        rpe_score     = avg_rpe / 10.0
        exp_score     = min(weeks_active, 52) / 52.0
        fitness_score = fitness_sc / 2.0

        score = (rpe_score * 0.50) + (exp_score * 0.30) + (fitness_score * 0.20)

        # Safety override: high RPE + beginner = overreaching risk
        if avg_rpe > 8.5 and fitness_sc == 0:
            intensity = 'low_intensity'
        elif score < 0.35:
            intensity = 'low_intensity'
        elif score < 0.62:
            intensity = 'moderate_intensity'
        else:
            intensity = 'high_intensity'

        confidence = self._confidence(score, intensity)

        return {
            'intensity':    intensity,
            'confidence':   confidence,
            'score':        round(score, 3),
            'adjustments':  ADJUSTMENTS[intensity],
            'avg_rpe':      round(avg_rpe, 1),
            'weeks_active': weeks_active,
            'data_points':  len(logs),
            'ml_note':      self._note(intensity, avg_rpe, weeks_active),
            'rpe_trend':    self._rpe_trend(logs),
        }

    def suggest_weight(self, exercise_name, logs, user_profile):
        ex_logs = [l for l in logs
                   if l.get('exercise_name', '').lower() == exercise_name.lower()]
        if not ex_logs:
            bw   = user_profile.get('weight_kg', 70)
            lvl  = user_profile.get('fitness_level', 'beginner')
            mult = {'beginner': 0.20, 'intermediate': 0.35, 'advanced': 0.55}
            return round(bw * mult.get(lvl, 0.20), 1), 'Starting estimate from bodyweight'
        pred    = self.predict_intensity(user_profile, logs)
        last_wt = ex_logs[-1].get('weight_kg', 0)
        add     = pred['adjustments']['weight_add']
        return round(last_wt + add, 1), f"Last: {last_wt} kg + {add} kg ({pred['intensity'].replace('_',' ')})"

    def get_adaptation_history(self, logs, days_per_week=3):
        """
        Returns week-by-week intensity history for the AI Insights screen.
        Shows how the model's prediction has changed as data accumulated.
        """
        if len(logs) < 3:
            return []

        history = []
        week_size = max(days_per_week, 1)

        for i in range(week_size, len(logs) + 1, week_size):
            subset   = logs[:i]
            avg_rpe  = self._avg_rpe(subset)
            weeks    = i // week_size
            score    = (avg_rpe / 10.0 * 0.50) + (min(weeks, 52) / 52.0 * 0.30)

            if score < 0.35:
                intensity = 'Low'
            elif score < 0.62:
                intensity = 'Moderate'
            else:
                intensity = 'High'

            history.append({
                'week':      weeks,
                'intensity': intensity,
                'avg_rpe':   round(avg_rpe, 1),
                'sessions':  i,
            })

        return history

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _avg_rpe(self, logs):
        vals = [l['rpe'] for l in logs[-10:] if l.get('rpe') is not None]
        return float(np.mean(vals)) if vals else 6.0

    def _rpe_trend(self, logs):
        """Returns 'rising', 'falling', or 'stable' based on last 6 RPE values."""
        vals = [l['rpe'] for l in logs[-6:] if l.get('rpe') is not None]
        if len(vals) < 3:
            return 'stable'
        first_half = np.mean(vals[:len(vals)//2])
        second_half = np.mean(vals[len(vals)//2:])
        diff = second_half - first_half
        if diff > 0.5:
            return 'rising'
        elif diff < -0.5:
            return 'falling'
        return 'stable'

    def _confidence(self, score, intensity):
        boundaries = {'low_intensity': 0.35, 'moderate_intensity': 0.62, 'high_intensity': 1.0}
        b = boundaries[intensity]
        if intensity == 'low_intensity':
            dist = b - score
        elif intensity == 'moderate_intensity':
            dist = min(score - 0.35, 0.62 - score)
        else:
            dist = score - 0.62
        return round(min(100, max(25, int(dist / 0.35 * 100))), 1)

    def _note(self, intensity, avg_rpe, weeks):
        if intensity == 'low_intensity':
            return f'Avg RPE {avg_rpe} over {weeks} weeks suggests fatigue. Plan adjusted for recovery.'
        elif intensity == 'moderate_intensity':
            return f'Consistent training for {weeks} weeks with avg RPE {avg_rpe}. Maintaining load.'
        else:
            return f'{weeks} weeks logged, avg RPE {avg_rpe}. Progression applied — ready to push harder.'
