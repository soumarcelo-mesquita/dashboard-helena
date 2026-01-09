import requests
import streamlit as st
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Helena CRM API Base URL
BASE_URL = "https://api.helena.run/crm/v1"

class HelenaAPIClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("HELENA_API_TOKEN")
        # No sampleCode.js o token é passado diretamente no header Authorization
        self.headers = {
            "Authorization": self.token,
            "accept": "application/json"
        }

    @st.cache_data(ttl=900) # 15 minutes TTL
    def get_cards(_self, panel_id: str) -> List[Dict[str, Any]]:
        """
        Busca todos os cards de um painel específico, lidando com paginação.
        """
        all_cards = []
        page = 1
        page_size = 50 
        
        while True:
            # PascalCase parameters as used in sampleCode.js
            params = {
                "PanelId": panel_id,
                "PageNumber": page,
                "PageSize": page_size,
                "IncludeDetails": "StepTitle"
            }
            
            try:
                response = requests.get(f"{BASE_URL}/panel/card", headers=_self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                all_cards.extend(items)
                
                if not data.get("hasMorePages", False):
                    break
                
                page += 1
            except Exception as e:
                st.error(f"Erro ao buscar cards na página {page}: {e}")
                break
                
        return all_cards

    @st.cache_data(ttl=3600) # Painéis mudam menos, cache de 1h
    def get_panels(_self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de painéis disponíveis.
        """
        try:
            response = requests.get(f"{BASE_URL}/panel", headers=_self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Erro ao buscar painéis: {e}")
            return []

    def clear_cache(self):
        """Invalida o cache do Streamlit"""
        st.cache_data.clear()
