#!/usr/bin/env python3
"""
🚀 SKINLYTICS AGGREGATION SERVICE
Serviço de agregações automáticas para insights ultra-rápidos
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, and_, text
from sqlalchemy.exc import IntegrityError

# Importar modelos otimizados
from src.models.optimized_database import (
    get_session, 
    Skin as OptimizedSkin, 
    ListingOptimized, 
    PriceHistory, 
    MarketInsights
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AggregationService:
    """Serviço de agregações automáticas para analytics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = get_session()
        
        # Estatísticas de agregação
        self.stats = {
            'price_history_created': 0,
            'insights_updated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info("🔄 Aggregation Service inicializado")
    
    def create_daily_price_history(self, target_date: Optional[datetime] = None) -> bool:
        """Cria agregações diárias de preços"""
        try:
            if not target_date:
                target_date = datetime.now().date()
            
            self.logger.info(f"📈 Criando histórico diário para {target_date}")
            
            # Query para agregações por skin e dia
            aggregation_query = """
            INSERT INTO price_history (skin_id, date, avg_price, min_price, max_price, volume, avg_float)
            SELECT 
                l.skin_id,
                DATE(l.collected_at) as date,
                AVG(l.price) as avg_price,
                MIN(l.price) as min_price,
                MAX(l.price) as max_price,
                COUNT(*) as volume,
                AVG(l.float_value) as avg_float
            FROM listings_optimized l
            WHERE DATE(l.collected_at) = :target_date
                AND l.price > 0
                AND l.skin_id IS NOT NULL
            GROUP BY l.skin_id, DATE(l.collected_at)
            ON CONFLICT (skin_id, date) DO UPDATE SET
                avg_price = EXCLUDED.avg_price,
                min_price = EXCLUDED.min_price,
                max_price = EXCLUDED.max_price,
                volume = EXCLUDED.volume,
                avg_float = EXCLUDED.avg_float
            """
            
            result = self.session.execute(
                text(aggregation_query), 
                {'target_date': target_date}
            )
            
            self.session.commit()
            self.stats['price_history_created'] += result.rowcount
            
            self.logger.info(f"✅ {result.rowcount} registros de histórico criados")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"❌ Erro ao criar histórico diário: {e}")
            self.stats['errors'] += 1
            return False
    
    def calculate_price_trends(self, skin_id: int) -> Dict:
        """Calcula tendências de preço para uma skin"""
        try:
            # Preços dos últimos 30 dias
            thirty_days_ago = datetime.now() - timedelta(days=30)
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # Preço atual (média das últimas 24h)
            current_price = self.session.query(func.avg(ListingOptimized.price)).filter(
                and_(
                    ListingOptimized.skin_id == skin_id,
                    ListingOptimized.collected_at >= datetime.now() - timedelta(hours=24),
                    ListingOptimized.price > 0
                )
            ).scalar()
            
            # Preço 7 dias atrás
            price_7d_ago = self.session.query(func.avg(PriceHistory.avg_price)).filter(
                and_(
                    PriceHistory.skin_id == skin_id,
                    PriceHistory.date >= seven_days_ago.date(),
                    PriceHistory.date < (seven_days_ago + timedelta(days=1)).date()
                )
            ).scalar()
            
            # Preço 30 dias atrás
            price_30d_ago = self.session.query(func.avg(PriceHistory.avg_price)).filter(
                and_(
                    PriceHistory.skin_id == skin_id,
                    PriceHistory.date >= thirty_days_ago.date(),
                    PriceHistory.date < (thirty_days_ago + timedelta(days=1)).date()
                )
            ).scalar()
            
            # Volume dos últimos 7 dias
            volume_7d = self.session.query(func.sum(PriceHistory.volume)).filter(
                and_(
                    PriceHistory.skin_id == skin_id,
                    PriceHistory.date >= seven_days_ago.date()
                )
            ).scalar() or 0
            
            # Calcular tendências
            trend_7d = 0
            trend_30d = 0
            
            if current_price and price_7d_ago and price_7d_ago > 0:
                trend_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
            
            if current_price and price_30d_ago and price_30d_ago > 0:
                trend_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
            
            # Liquidity score (volume/preço)
            liquidity_score = volume_7d / (current_price / 100) if current_price and current_price > 0 else 0
            
            return {
                'current_avg_price': current_price,
                'price_trend_7d': trend_7d,
                'price_trend_30d': trend_30d,
                'volume_trend_7d': volume_7d,
                'liquidity_score': liquidity_score
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular tendências para skin {skin_id}: {e}")
            return {}
    
    def calculate_opportunity_score(self, trends: Dict, skin_data: Dict) -> float:
        """Calcula score de oportunidade (0-100)"""
        try:
            score = 50.0  # Base score
            
            # Tendência de preço (peso: 30%)
            if trends.get('price_trend_7d'):
                if trends['price_trend_7d'] < -10:  # Queda de 10%+
                    score += 15
                elif trends['price_trend_7d'] < -5:  # Queda de 5-10%
                    score += 10
                elif trends['price_trend_7d'] > 10:  # Alta de 10%+
                    score -= 15
            
            # Volume/Liquidez (peso: 25%)
            liquidity = trends.get('liquidity_score', 0)
            if liquidity > 100:
                score += 12
            elif liquidity > 50:
                score += 8
            elif liquidity < 10:
                score -= 10
            
            # Raridade (peso: 20%)
            rarity = skin_data.get('rarity', 0)
            if rarity >= 6:  # Covert/Classified
                score += 10
            elif rarity >= 4:  # Restricted
                score += 5
            
            # StatTrak (peso: 15%)
            if skin_data.get('is_stattrak'):
                score += 7
            
            # Souvenir (peso: 10%)
            if skin_data.get('is_souvenir'):
                score += 5
            
            # Garantir range 0-100
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular opportunity score: {e}")
            return 50.0
    
    def update_market_insights(self) -> bool:
        """Atualiza insights de mercado para todas as skins"""
        try:
            self.logger.info("🧠 Atualizando market insights...")
            
            # Buscar todas as skins com listings recentes
            active_skins = self.session.query(OptimizedSkin).join(ListingOptimized).filter(
                ListingOptimized.collected_at >= datetime.now() - timedelta(days=7)
            ).distinct().all()
            
            insights_updated = 0
            
            for skin in active_skins:
                try:
                    # Calcular tendências
                    trends = self.calculate_price_trends(skin.id)
                    
                    if not trends.get('current_avg_price'):
                        continue
                    
                    # Dados da skin para opportunity score
                    skin_data = {
                        'rarity': skin.rarity,
                        'is_stattrak': skin.is_stattrak,
                        'is_souvenir': skin.is_souvenir
                    }
                    
                    # Calcular opportunity score
                    opportunity_score = self.calculate_opportunity_score(trends, skin_data)
                    
                    # Determinar se está subvalorizada
                    is_undervalued = (
                        trends.get('price_trend_7d', 0) < -5 and  # Queda recente
                        trends.get('volume_trend_7d', 0) > 5 and  # Volume alto
                        opportunity_score > 70                    # Score alto
                    )
                    
                    # Criar ou atualizar insight
                    existing_insight = self.session.query(MarketInsights).filter_by(
                        skin_id=skin.id
                    ).first()
                    
                    if existing_insight:
                        # Atualizar existente
                        existing_insight.current_avg_price = trends['current_avg_price']
                        existing_insight.price_trend_7d = trends.get('price_trend_7d', 0)
                        existing_insight.price_trend_30d = trends.get('price_trend_30d', 0)
                        existing_insight.volume_trend_7d = trends.get('volume_trend_7d', 0)
                        existing_insight.liquidity_score = trends.get('liquidity_score', 0)
                        existing_insight.is_undervalued = is_undervalued
                        existing_insight.opportunity_score = opportunity_score
                        existing_insight.last_updated = datetime.now()
                    else:
                        # Criar novo
                        new_insight = MarketInsights(
                            skin_id=skin.id,
                            current_avg_price=trends['current_avg_price'],
                            price_trend_7d=trends.get('price_trend_7d', 0),
                            price_trend_30d=trends.get('price_trend_30d', 0),
                            volume_trend_7d=trends.get('volume_trend_7d', 0),
                            liquidity_score=trends.get('liquidity_score', 0),
                            is_undervalued=is_undervalued,
                            opportunity_score=opportunity_score,
                            last_updated=datetime.now()
                        )
                        self.session.add(new_insight)
                    
                    insights_updated += 1
                    
                    if insights_updated % 50 == 0:
                        self.logger.info(f"📊 {insights_updated} insights processados...")
                        self.session.commit()  # Commit parcial
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao processar skin {skin.id}: {e}")
                    continue
            
            self.session.commit()
            self.stats['insights_updated'] = insights_updated
            
            self.logger.info(f"✅ {insights_updated} market insights atualizados")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"❌ Erro ao atualizar insights: {e}")
            self.stats['errors'] += 1
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Remove dados antigos para manter performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Remover price history muito antigo
            old_history = self.session.query(PriceHistory).filter(
                PriceHistory.date < cutoff_date.date()
            ).delete()
            
            self.session.commit()
            
            if old_history > 0:
                self.logger.info(f"🧹 Removidos {old_history} registros antigos de price_history")
            
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"❌ Erro no cleanup: {e}")
            return False
    
    def run_daily_aggregation(self) -> Dict:
        """Executa agregação diária completa"""
        try:
            self.logger.info("🚀 Iniciando agregação diária...")
            
            # Reset stats
            self.stats = {
                'price_history_created': 0,
                'insights_updated': 0,
                'errors': 0,
                'start_time': datetime.now()
            }
            
            # 1. Criar histórico de preços diário
            self.create_daily_price_history()
            
            # 2. Atualizar insights de mercado
            self.update_market_insights()
            
            # 3. Cleanup de dados antigos
            self.cleanup_old_data()
            
            # Calcular tempo total
            duration = datetime.now() - self.stats['start_time']
            
            self.logger.info(f"✅ Agregação diária concluída em {duration}")
            
            return {
                'success': True,
                'duration': duration.total_seconds(),
                'stats': self.stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na agregação diária: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
        
        finally:
            self.session.close()
    
    def get_top_opportunities(self, limit: int = 20) -> List[Dict]:
        """Retorna top oportunidades do mercado"""
        try:
            session = get_session()
            
            top_opportunities = session.query(
                MarketInsights, OptimizedSkin
            ).join(OptimizedSkin).filter(
                MarketInsights.opportunity_score > 60,
                MarketInsights.last_updated >= datetime.now() - timedelta(hours=24)
            ).order_by(
                MarketInsights.opportunity_score.desc()
            ).limit(limit).all()
            
            results = []
            for insight, skin in top_opportunities:
                results.append({
                    'skin_name': skin.market_hash_name,
                    'current_price': insight.current_avg_price / 100,  # Convert to USD
                    'trend_7d': insight.price_trend_7d,
                    'trend_30d': insight.price_trend_30d,
                    'volume_7d': insight.volume_trend_7d,
                    'liquidity_score': insight.liquidity_score,
                    'opportunity_score': insight.opportunity_score,
                    'is_undervalued': insight.is_undervalued,
                    'rarity': skin.rarity,
                    'is_stattrak': skin.is_stattrak
                })
            
            session.close()
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar oportunidades: {e}")
            return []

def main():
    """Função principal para execução standalone"""
    service = AggregationService()
    result = service.run_daily_aggregation()
    
    if result['success']:
        print("✅ Agregação concluída com sucesso!")
        print(f"📊 Estatísticas: {result['stats']}")
    else:
        print(f"❌ Erro na agregação: {result['error']}")

if __name__ == "__main__":
    main()