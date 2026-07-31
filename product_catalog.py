PRODUCT_DB = {
    'Smartphone': {
        'Apple': {
            'iPhone 17': ['iPhone 17', 'iPhone 17 Pro', 'iPhone 17 Pro Max'],
            'iPhone 16': ['iPhone 16', 'iPhone 16 Pro', 'iPhone 16 Pro Max'],
            'iPhone 15': ['iPhone 15', 'iPhone 15 Pro']
        },
        'Samsung': {
            'Galaxy S26': ['Galaxy S26', 'Galaxy S26+', 'Galaxy S26 Ultra'],
            'Galaxy S25': ['Galaxy S25', 'Galaxy S25 Ultra'],
            'Galaxy A': ['Galaxy A56'],
            'Galaxy Z': ['Galaxy Z Flip 7']
        },
        'Google': {
            'Pixel 10': ['Pixel 10', 'Pixel 10 Pro'],
            'Pixel 9': ['Pixel 9 Pro'],
            'Pixel 8': ['Pixel 8a']
        },
        'Xiaomi': {
            'Xiaomi 16': ['Xiaomi 16 Pro'],
            'Xiaomi 15': ['Xiaomi 15'],
            'Redmi': ['Redmi Note 15'],
            'Poco': ['Poco X7']
        },
        'OnePlus': {
            'OnePlus 14': ['OnePlus 14'],
            'OnePlus 13': ['OnePlus 13'],
            'Nord': ['Nord 5']
        },
        'Sony': {
            'Xperia 1': ['Xperia 1 VII'],
            'Xperia 5': ['Xperia 5 VII']
        },
        'Andere': {}
    },
    'Kopfhörer': {
        'Apple': {
            'AirPods Pro': ['AirPods Pro (3. Gen)'],
            'AirPods': ['AirPods (4. Gen)'],
            'AirPods Max': ['AirPods Max 2'],
            'Beats': ['Beats Fit Pro']
        },
        'Samsung': {
            'Galaxy Buds': ['Galaxy Buds 3 Pro', 'Galaxy Buds FE']
        },
        'Sony': {
            'WF (In-Ear)': ['WF-1000XM6'],
            'WH (Over-Ear)': ['WH-1000XM6'],
            'LinkBuds': ['LinkBuds']
        },
        'Bose': {
            'QuietComfort': ['QuietComfort Ultra', 'QC Earbuds']
        },
        'JBL': {
            'Tour': ['Tour Pro 3'],
            'Live': ['Live Pro 2'],
            'Wave': ['Wave Beam']
        },
        'Sennheiser': {
            'Momentum': ['Momentum True Wireless 4', 'Momentum 4 Over-Ear']
        },
        'Andere': {}
    },
    'Laptop/Tablet': {
        'Apple': {
            'MacBook Air': ['MacBook Air M4'],
            'MacBook Pro': ['MacBook Pro M4'],
            'iPad Pro': ['iPad Pro (M4)'],
            'iPad Air': ['iPad Air']
        },
        'Lenovo': {
            'ThinkPad': ['ThinkPad X1 Carbon'],
            'IdeaPad': ['IdeaPad'],
            'Yoga': ['Yoga']
        },
        'HP': {
            'Spectre': ['Spectre x360'],
            'Envy': ['Envy'],
            'Pavilion': ['Pavilion']
        },
        'Dell': {
            'XPS': ['XPS 13', 'XPS 15'],
            'Inspiron': ['Inspiron']
        },
        'Microsoft': {
            'Surface Pro': ['Surface Pro 12'],
            'Surface Laptop': ['Surface Laptop 7']
        },
        'Samsung': {
            'Galaxy Book': ['Galaxy Book 5'],
            'Galaxy Tab': ['Galaxy Tab S10']
        },
        'Andere': {}
    }
}

COLOR_OPTIONS = ['Schwarz', 'Weiß', 'Silber', 'Grau', 'Blau', 'Rot', 'Grün', 'Gold', 'Rosé/Pink', 'Bunt']

CASE_OPTIONS_BY_CATEGORY = {
    'Smartphone': {'label': 'Hülle/Case', 'options': ['Keine Hülle', 'Transparente Hülle', 'Bunte Hülle', 'Lederhülle', 'Sonstige Hülle']},
    'Kopfhörer': {'label': 'Ladecase', 'options': ['Case dabei', 'Case fehlt']},
    'Laptop/Tablet': {'label': 'Hülle/Tasche', 'options': ['Keine Hülle', 'Sleeve/Tasche', 'Keyboard-Case', 'Sonstige Hülle']},
    'Brille': {'label': 'Brillenetui', 'options': ['Etui dabei', 'Kein Etui']},
    'Tasche': {'label': 'Zustand', 'options': ['Neuwertig', 'Gebraucht', 'Stark abgenutzt']}
}