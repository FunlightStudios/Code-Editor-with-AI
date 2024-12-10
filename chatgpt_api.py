import os
from openai import OpenAI, RateLimitError
from PySide6.QtWidgets import QInputDialog, QLineEdit

class ChatGPTAPI:
    def __init__(self):
        self.client = None
        self.api_key = self._get_api_key()
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def _get_api_key(self):
        """Holt den API-Key aus der Umgebungsvariable oder fragt nach."""
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            api_key, ok = QInputDialog.getText(
                None,
                "OpenAI API-Key",
                "Bitte geben Sie Ihren OpenAI API-Key ein:",
                QLineEdit.Password
            )
            if ok and api_key:
                os.environ['OPENAI_API_KEY'] = api_key
            else:
                return None
                
        return api_key

    def _handle_api_error(self, error):
        """Behandelt API-Fehler und gibt Fehlermeldungen zurück."""
        if isinstance(error, RateLimitError):
            return "⚠️ Das API-Limit wurde erreicht. Bitte versuchen Sie es in einer Stunde erneut oder upgraden Sie auf einen Pro-Account."
        else:
            error_msg = str(error)
            if "api_key" in error_msg.lower():
                return "⚠️ Der API-Key ist ungültig. Bitte überprüfen Sie Ihren API-Key."
            else:
                return f"⚠️ API-Fehler: {error_msg}"

    def chat(self, message, code_context=None):
        """Allgemeine Chat-Funktion mit oder ohne Code-Kontext."""
        if not self.client:
            return "API nicht initialisiert. Bitte API-Key eingeben."
            
        try:
            messages = [
                {"role": "system", "content": "Du bist ein hilfreicher Code-Assistent namens Windsurf AI. "
                 "Du hilfst Benutzern sowohl bei Code-Fragen als auch bei allgemeinen Themen. "
                 "Antworte freundlich und präzise auf Deutsch."}
            ]
            
            if code_context:
                messages.append({"role": "system", "content": f"Aktueller Code-Kontext:\n{code_context}"})
            
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e)

    def analyze_code(self, code):
        """Analysiert den gegebenen Code."""
        if not self.client:
            return "API nicht initialisiert. Bitte API-Key eingeben."
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Code-Analyse-Assistent von Windsurf AI. "
                     "Analysiere den Code präzise und gib hilfreiche Verbesserungsvorschläge auf Deutsch."},
                    {"role": "user", "content": f"Analysiere diesen Code:\n\n{code}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e)

    def get_code_suggestions(self, code, query):
        """Holt Vorschläge basierend auf Code und Anfrage."""
        if not self.client:
            return "API nicht initialisiert. Bitte API-Key eingeben."
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein hilfreicher Code-Assistent von Windsurf AI. "
                     "Gib präzise und praktische Vorschläge auf Deutsch."},
                    {"role": "user", "content": f"Code:\n{code}\n\nAnfrage: {query}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e)

    def get_code_edit_suggestion(self, code, instruction):
        """Holt Vorschläge für Code-Änderungen."""
        if not self.client:
            return "API nicht initialisiert. Bitte API-Key eingeben."
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Code-Bearbeitungs-Assistent von Windsurf AI. "
                     "Schlage präzise und praktische Code-Änderungen auf Deutsch vor."},
                    {"role": "user", "content": f"Bearbeite diesen Code gemäß der Anweisung:\n\nCode:\n{code}\n\nAnweisung: {instruction}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e)
