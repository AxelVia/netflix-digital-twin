"""
Starbucks SEC Data Collector
Collecte des données financières depuis EDGAR
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime
import os

class StarbucksDataCollector:
    def __init__(self):
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.headers = {
            'User-Agent': 'AxelVia aviard.work@gmail.com'  # Requis par SEC
        }
        self.cik = "0000829224" 
        
    def get_company_facts(self):
        """Récupère toutes les données financières Starbucks"""
        url = f"{self.base_url}/CIK{self.cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API SEC: {e}")
            return None
    
    def extract_key_metrics(self, company_facts):
        """Extrait les métriques clés"""
        if not company_facts:
            return None
            
        facts = company_facts['facts']['us-gaap']
        
        # Métriques à extraire
        metrics = {
            'Revenues': 'Revenues',
            'NetIncomeLoss': 'NetIncomeLoss', 
            'Assets': 'Assets',
            'StockholdersEquity': 'StockholdersEquity',
            'OperatingIncomeLoss': 'OperatingIncomeLoss'
        }
        
        data = []
        
        for metric_name, sec_field in metrics.items():
            if sec_field in facts:
                for unit_type, values in facts[sec_field]['units'].items():
                    if unit_type == 'USD':  # Données en dollars
                        for item in values:
                            if item.get('form') in ['10-K', '10-Q']:
                                data.append({
                                    'metric': metric_name,
                                    'value': item['val'],
                                    'date': item['end'],
                                    'period': item['fp'],
                                    'form': item['form'],
                                    'year': datetime.strptime(item['end'], '%Y-%m-%d').year
                                })
        
        return pd.DataFrame(data)
    
    def get_store_count_data(self, company_facts):
        """Extrait les données de nombre de magasins depuis les filings"""
        # Cette fonction nécessitera du parsing des 10-K pour les détails géographiques
        # Pour l'instant, on retourne une structure vide
        return pd.DataFrame()
    
    def save_data(self, df, filename):
        """Sauvegarde les données"""
        os.makedirs('data/raw/financial', exist_ok=True)
        filepath = f'data/raw/financial/{filename}'
        df.to_csv(filepath, index=False)
        print(f"Données sauvées: {filepath}")
    
    def collect_all_data(self):
        """Collecte complète des données"""
        print("Collecte des données SEC pour Starbucks...")
        
        # Récupération des facts
        company_facts = self.get_company_facts()
        
        if not company_facts:
            print("Échec de collecte")
            return
        
        # Extraction métriques financières
        financial_df = self.extract_key_metrics(company_facts)
        
        if financial_df is not None and not financial_df.empty:
            self.save_data(financial_df, 'starbucks_financial_metrics.csv')
            print(f"Collecté {len(financial_df)} points de données financières")
            
            # Résumé par année
            summary = financial_df.groupby(['year', 'metric'])['value'].sum().unstack()
            print("\nRésumé revenus par année:")
            if 'Revenues' in summary.columns:
                print(summary['Revenues'].dropna().tail(10))
        
        # Sauvegarde des données brutes
        with open('data/raw/financial/starbucks_raw_facts.json', 'w') as f:
            json.dump(company_facts, f, indent=2)
        
        return financial_df

if __name__ == "__main__":
    collector = StarbucksDataCollector()
    data = collector.collect_all_data()