"""
theme.py — Light / Dark mode color system.
All UI colors are read from here.
Toggle theme by calling set_theme('light') or set_theme('dark').
"""

THEMES = {
    'light': {
        # Backgrounds
        'bg':          (0.949, 0.957, 0.969, 1),   # #F2F4F7
        'surface':     (1,     1,     1,     1),   # #FFFFFF
        'card':        (1,     1,     1,     1),   # #FFFFFF
        'card2':       (0.961, 0.965, 0.973, 1),   # #F5F6F8
        'header':      (0.051, 0.106, 0.165, 1),   # #0D1B2A navy

        # Borders & dividers
        'border':      (0.878, 0.890, 0.910, 1),   # #E0E3E8
        'divider':     (0.925, 0.933, 0.945, 1),   # #ECEFF1

        # Text
        'text':        (0.051, 0.106, 0.165, 1),   # #0D1B2A
        'text2':       (0.380, 0.420, 0.490, 1),   # #616B7D
        'text3':       (0.620, 0.650, 0.700, 1),   # #9EA6B2

        # Accent — blue
        'blue':        (0.145, 0.388, 0.922, 1),   # #2563EB
        'blue_dim':    (0.929, 0.941, 0.996, 1),   # #EDF0FE
        'blue_text':   (0.145, 0.388, 0.922, 1),   # #2563EB

        # Status
        'green':       (0.129, 0.686, 0.392, 1),   # #21AF64
        'green_dim':   (0.902, 0.969, 0.929, 1),   # #E6F7ED
        'red':         (0.918, 0.263, 0.208, 1),   # #EB4335
        'red_dim':     (0.996, 0.910, 0.902, 1),   # #FEE8E7
        'amber':       (0.957, 0.647, 0.082, 1),   # #F4A515
        'amber_dim':   (0.996, 0.953, 0.878, 1),   # #FEF3E0
        'purple':      (0.502, 0.271, 0.918, 1),   # #8045EA
        'purple_dim':  (0.937, 0.910, 0.996, 1),   # #EFE8FE

        # Nav bar
        'nav_bg':      (1,     1,     1,     1),
        'nav_border':  (0.878, 0.890, 0.910, 1),
        'nav_active':  (0.145, 0.388, 0.922, 1),
        'nav_inactive':(0.620, 0.650, 0.700, 1),

        # Shadow (simulated with border)
        'shadow':      (0.878, 0.890, 0.910, 1),
    },

    'dark': {
        # Backgrounds
        'bg':          (0.051, 0.067, 0.090, 1),   # #0D1117
        'surface':     (0.086, 0.102, 0.133, 1),   # #161B22
        'card':        (0.110, 0.129, 0.157, 1),   # #1C2128
        'card2':       (0.129, 0.149, 0.180, 1),   # #212526
        'header':      (0.051, 0.067, 0.090, 1),   # #0D1117

        # Borders
        'border':      (0.188, 0.212, 0.255, 1),   # #303641
        'divider':     (0.157, 0.180, 0.216, 1),   # #282E37

        # Text
        'text':        (0.902, 0.929, 0.953, 1),   # #E6EDF3
        'text2':       (0.545, 0.580, 0.620, 1),   # #8B949E
        'text3':       (0.282, 0.310, 0.345, 1),   # #484F58

        # Accent — blue
        'blue':        (0.216, 0.529, 0.992, 1),   # #3787FD
        'blue_dim':    (0.086, 0.149, 0.259, 1),   # #162642
        'blue_text':   (0.345, 0.651, 1.000, 1),   # #58A6FF

        # Status
        'green':       (0.247, 0.725, 0.314, 1),   # #3FB950
        'green_dim':   (0.063, 0.196, 0.098, 1),   # #103219
        'red':         (0.973, 0.318, 0.286, 1),   # #F85149
        'red_dim':     (0.235, 0.082, 0.075, 1),   # #3C1513
        'amber':       (0.824, 0.600, 0.133, 1),   # #D29922
        'amber_dim':   (0.200, 0.149, 0.047, 1),   # #33260C
        'purple':      (0.737, 0.549, 1.000, 1),   # #BC8CFF
        'purple_dim':  (0.157, 0.102, 0.235, 1),   # #28193C

        # Nav bar
        'nav_bg':      (0.086, 0.102, 0.133, 1),
        'nav_border':  (0.188, 0.212, 0.255, 1),
        'nav_active':  (0.345, 0.651, 1.000, 1),
        'nav_inactive':(0.420, 0.455, 0.510, 1),

        'shadow':      (0.000, 0.000, 0.000, 0.3),
    }
}

_current = 'light'

def get(key):
    return THEMES[_current].get(key, (1, 1, 1, 1))

def set_theme(mode):
    global _current
    if mode in THEMES:
        _current = mode

def current():
    return _current

def toggle():
    global _current
    _current = 'dark' if _current == 'light' else 'light'
    return _current
