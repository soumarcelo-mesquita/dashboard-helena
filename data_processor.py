import pandas as pd
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

class DataProcessor:
    def __init__(self, tags_file: str = "tags.json", steps_file: str = "steps.json"):
        self.tags_map = self._load_json(tags_file)
        self.steps_map = self._load_json(steps_file)
        # Usaremos o steps_map para definir a ORDEM do funil, removendo etapas finais conforme pedido
        self.step_order = [s for s in self.steps_map.keys() if s not in ["Concluído", "No Deal"]]

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_aging_group(self, updatedAt_str: str) -> str:
        # Lógica vinda do sampleCode.js
        try:
            updatedAt = pd.to_datetime(updatedAt_str)
            now = datetime.now(timezone.utc)
            # Garantir que updatedAt é timezone aware se o pandas não o fez automaticamente
            if updatedAt.tzinfo is None:
                updatedAt = updatedAt.replace(tzinfo=timezone.utc)
            
            diff_ms = now - updatedAt
            days = diff_ms.days

            if days == 0: return "Hoje"
            if days <= 2: return "48 horas"
            if days <= 7: return "7 dias"
            if days <= 15: return "15 dias"

            return "Mais de 15 dias"
        except:
            return "N/A"

    def get_action_type(self, tag_names: List[str]) -> str:
        # Lógica vinda do sampleCode.js
        if '258' in tag_names: return '258'
        if '439' in tag_names: return '439'
        if 'FUNASA' in tag_names: return 'FUNASA'
        if 'CARPH' in tag_names: return 'CARPH'
        return ''

    def process_cards(self, cards: List[Dict[str, Any]]) -> pd.DataFrame:
        if not cards:
            return pd.DataFrame()
            
        df = pd.DataFrame(cards)
        
        # Converter datas
        df["createdAt"] = pd.to_datetime(df["createdAt"])
        df["updatedAt"] = pd.to_datetime(df["updatedAt"])
        
        # Mapear Tag Names
        df["tagNames"] = df["tagIds"].apply(lambda ids: [self.tags_map.get(tid, tid) for tid in ids] if isinstance(ids, list) else [])
        
        # Action Type (visto no sampleCode.js)
        df["actionType"] = df["tagNames"].apply(self.get_action_type)
        
        # Aging Group (visto no sampleCode.js)
        df["age_group"] = df["updatedAt"].apply(lambda x: self.get_aging_group(str(x)))
        
        # Calcular dias no status atual para cálculos numéricos
        now = datetime.now(timezone.utc)
        df["days_in_status"] = (now - df["updatedAt"]).dt.days
        
        return df

    def get_status_pivot_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Quantidade de cards por status pivotada por aging group"""
        if df.empty:
            return pd.DataFrame()
            
        # Ordem específica do aging group (sampleCode.js)
        age_order = ["Hoje", "48 horas", "7 dias", "15 dias", "Mais de 15 dias"]
        
        # Garantir que o pivot use a ordem correta
        pivot = df.pivot_table(
            index="stepTitle", 
            columns="age_group", 
            values="id", 
            aggfunc="count", 
            fill_value=0
        )
        
        # Reordenar colunas conforme lógica de negócio
        existing_cols = [col for col in age_order if col in pivot.columns]
        pivot = pivot[existing_cols]
        
        # Reordenar linhas conforme steps_map (se os nomes baterem)
        existing_rows = [row for row in self.step_order if row in pivot.index]
        if existing_rows:
            pivot = pivot.reindex(existing_rows)
            
        return pivot

    def get_tag_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Distribuição de valor por etiquetas (tags) mapeadas"""
        if df.empty:
            return pd.DataFrame()
            
        # Explodir tagNames
        df_tags = df.explode("tagNames")
        df_tags = df_tags.dropna(subset=["tagNames"])
            
        tag_val = df_tags.groupby("tagNames")["monetaryAmount"].sum().reset_index()
        tag_val.columns = ["Tag", "Valor Total"]
        return tag_val.sort_values("Valor Total", ascending=False)

    def get_conversion_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara dados para o funil ordenado pelos steps definidos"""
        if df.empty:
            return pd.DataFrame()
            
        # Agrupar por etapa e contar
        funnel = df.groupby("stepTitle")["id"].count().reset_index()
        funnel.columns = ["Etapa", "Quantidade"]
        
        # Criar categoria ordenada
        funnel["Etapa"] = pd.Categorical(funnel["Etapa"], categories=self.step_order, ordered=True)
        return funnel.sort_values("Etapa").dropna(subset=["Etapa"])

    def get_velocity_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula velocidade do pipeline"""
        if df.empty:
            return {"avg_total_days": 0, "total_value": 0, "card_count": 0}
            
        now = datetime.now(timezone.utc)
        avg_days = (now - df["createdAt"]).dt.days.mean()
        
        return {
            "avg_total_days": round(avg_days, 1),
            "total_value": df["monetaryAmount"].sum(),
            "card_count": len(df)
        }
