import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

class Visualizer:
    @staticmethod
    def plot_funnel(df_funnel: pd.DataFrame, title: str = "Funil de Vendas"):
        """Gráfico de Funil (Quantidade ou Valor)"""
        is_monetary = df_funnel["Quantidade"].mean() > 1000 # Heurística simples
        
        fig = px.funnel(df_funnel, x="Quantidade", y="Etapa", title=title)
        
        if is_monetary:
            fig.update_traces(texttemplate="R$ %{value:,.2f}")
        else:
            fig.update_traces(texttemplate="%{value}")
            
        fig.update_layout(template="plotly_dark", separators=',.')
        return fig

    @staticmethod
    def plot_avg_time_by_step(df: pd.DataFrame, threshold_slow: int = 15):
        """Gráfico de barras horizontal com cores para gargalos, removendo etapas finais"""
        # Filtrar etapas conforme solicitado
        exclude_steps = ["Concluído", "No Deal"]
        df_filtered = df[~df["stepTitle"].isin(exclude_steps)].copy()
        
        if df_filtered.empty:
            return None
            
        avg_time = df_filtered.groupby("stepTitle")["days_in_status"].mean().reset_index()
        avg_time.columns = ["Etapa", "Tempo Médio (Dias)"]
        
        # Definir cores based no threshold
        avg_time["Cor"] = avg_time["Tempo Médio (Dias)"].apply(
            lambda x: "Red" if x > threshold_slow else "Blue"
        )
        
        fig = px.bar(
            avg_time, 
            x="Tempo Médio (Dias)", 
            y="Etapa", 
            orientation="h",
            color="Cor",
            color_discrete_map={"Red": "#ef553b", "Blue": "#636efa"},
            title="Tempo Médio em cada Etapa (Excluindo Finalizadas)"
        )
        fig.update_layout(template="plotly_dark", showlegend=False, separators=',.')
        return fig

    @staticmethod
    def plot_tag_treemap(df_tag: pd.DataFrame):
        """Treemap de valor por tag"""
        if df_tag.empty:
            return None
        fig = px.treemap(
            df_tag, 
            path=["Tag"], 
            values="Valor Total",
            title="Distribuição de Valor por Etiqueta"
        )
        fig.update_layout(template="plotly_dark", separators=',.')
        return fig

    @staticmethod
    def plot_entry_exit_trends(df: pd.DataFrame):
        """Gráfico de linhas entrada vs saída (simulado se não houver data de fechamento)"""
        # Como não temos explicitamente "exitDate" no sample, vamos usar createdAt como entrada
        df_entry = df.copy()
        df_entry["date"] = df_entry["createdAt"].dt.date
        trend = df_entry.groupby("date")["id"].count().reset_index()
        trend.columns = ["Data", "Novos Cards"]
        
        fig = px.line(trend, x="Data", y="Novos Cards", title="Tendência de Entrada de Novos Cards")
        fig.update_layout(template="plotly_dark")
        return fig

    @staticmethod
    def plot_conversion_by_tag(df: pd.DataFrame):
        """Taxa de conversão por tipo de assunto (tag)"""
        # Simulação de conversão (cards na ultima etapa / total)
        # Precisaríamos saber qual etapa é "Fechado"
        return None # Implementar conforme lógica de negócio definida
