# Definition der Datenstruktur für die MongoDB-Collection 'fundmeldung'
# Erstellt als Python-Dictionary zur Repräsentation eines MVP-Dokuments.

beispiel_fundmeldung = {
    "objekt_typ": "Brieftasche",        # Kategorie des Gegenstands (z.B. Handy, Schlüssel)
    "beschreibung": "Schwarze Lederbrieftasche mit Münzen, ohne Ausweis.", # Freitextbeschreibung
    "zeitpunkt": "2026-07-08 09:30",    # ISO-Zeitstempel der Ticketdarstellung
    "fundort_allgemein": "U-Bahnhof Mehringdamm, Berlin", # Standortdaten des Fundorts
    "foto_url": "/static/uploads/brieftasche.jpg", # Speicherpfad für die KI-Bildanalyse

    # Sicherheitsrelevante Zusatzdaten für sensible Wertsachen
    "abgegeben_bei_polizei": {
        "name": "Polizeiabschnitt 32",  # Identifikation der zuständigen Dienststelle
        "adresse": {
            "strasse": "Tempelhofer Damm 12",
            "plz": "12101",
            "ort": "Berlin"
        },
        "telefonnummer": "+49 30 123456", # Kontaktnummer im String-Format für Ländervorwahlen
        "vorgangsnummer": "VGs-2026-98765"
    }
}